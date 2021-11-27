import asyncio
import logging
from functools import wraps

from worker.parsers.exceptions import AccessFactoryException
from worker.parsers.utils import RichList
from worker.session.exceptions import NoTokenAvailableException, RpsLimitException, TokenAuthFailed


logger = logging.getLogger(__name__)


def items_getter(method):
    @wraps(method)
    async def wrapper(*args, **kwargs):
        result = await method(*args, **kwargs)
        if kwargs.get('raw_') and isinstance(result, dict):
            return result
        items = RichList(result.pop('items'))
        items.count_ = result.pop('count')
        items.data = result
        return items

    return wrapper


class MappedInterface:
    """
    Wraps method and give .sync interface to call async functions

    --------------------
    Async variant:

        async def abc(x):
            return x
        print(asyncio.run(abs()))
    --------------------
    Sync variant:

        @MakeSynced
        async def abc(x):
            return x

        print(abc.sync(3))
    """

    def __init__(self, _method):
        self._method = _method

    async def __call__(self, *args, **kwargs):
        return await self._method(*args, **kwargs)

    def sync(self, *args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(self._method(*args, **kwargs))

    async def map(self, items, **kwargs):
        return await asyncio.gather(
            *[self._method(item, **kwargs) for item in items],
            return_exceptions=True
        )

    def sync_map(self, items, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.map(items, **kwargs))


mapped_method = MappedInterface


def reliable_call(method):
    """Reply request if rps limit exceeded or tokens ended"""

    @wraps(method)
    async def wrapper(cls, *args, **kwargs):
        wait_time = 0.01
        while True:
            try:
                return await method(cls, *args, **kwargs)
            except RpsLimitException:
                if wait_time > 2:
                    logger.debug('RPS wait: %s', wait_time)
                wait_time *= 1.1
                await asyncio.sleep(wait_time)
                continue
            except TokenAuthFailed:
                logger.error(f'Token auth failed: {cls.__name__}')
                continue
            except NoTokenAvailableException:
                raise AccessFactoryException(f'Have no available tokens: {cls.__name__}')

    return wrapper

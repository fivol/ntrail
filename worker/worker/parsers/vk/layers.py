import asyncio
import logging
import time
from functools import wraps

from worker.session.exceptions import NoTokenAvailableException, RpsLimitException, TokenAuthFailed, TokenAccessDenied
from worker.helpers.tools import split_list

logger = logging.getLogger()


def partition_split(segment_size):
    """
    Assumes first argument of method is big list,
    splits it to several smaller lists of segment_size and calls this method again
    If input list is empty returns empty without making queries
    """

    def decorator(method):
        @wraps(method)
        async def wrapper(cls, items, **kwargs):
            assert isinstance(items, list)
            if not items:
                return []
            if len(items) <= segment_size:
                return await method(cls, items, **kwargs)
            items_parts = split_list(items, segment_size=segment_size)
            logger.debug('Split query into %s parts', len(items_parts))
            results_parts = await asyncio.gather(*[
                method(cls, partition, **kwargs) for partition in items_parts
            ])
            assert isinstance(results_parts[0], list)
            results = sum(results_parts, [])
            return results

        return wrapper

    return decorator


# TODO Make this decorator after all others in class (not it is before others)
def count_offset_iterator(max_count):
    """If passed too big "count", splits to several method calls
        Argument "percent_" can be passed with [0, 1] diapason to load part from full count
    """

    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            count = kwargs.pop('count', max_count) or max_count
            percent_ = kwargs.pop('percent_', None)
            all_ = kwargs.pop('all_', None)
            if all_:
                percent_ = 1

            if not percent_ and count <= max_count:
                return await method(*args, count=count, **kwargs)
            curr_offset = kwargs.pop('offset', 0)
            tasks = []
            first_call = []
            while count > 0:
                curr_count = min(count, max_count)
                if percent_:
                    first_call = await method(*args, **kwargs, offset=curr_offset, count=curr_count)
                    full_count = first_call.count_
                    count = int(full_count * percent_)
                    percent_ = None
                else:
                    tasks.append(method(*args, offset=curr_offset, count=curr_count))
                curr_offset += curr_count
                count -= curr_count
            result = await asyncio.gather(*tasks)
            return first_call + sum(result, ListWithCount())

        return wrapper

    return decorator


class ListWithCount(list):
    count_ = None

    def __add__(self, other):
        result = ListWithCount(super().__add__(other))
        result.count_ = self.count_ or getattr(other, 'count_')
        return result


def items_getter(method):
    @wraps(method)
    async def wrapper(*args, **kwargs):
        result = await method(*args, **kwargs)
        if kwargs.get('raw_') and isinstance(result, dict):
            return result
        items = ListWithCount(result.get('items'))
        items.count_ = result.get('count')
        return items

    return wrapper


class MakeSynced:
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
        raise DeprecationWarning()
        return loop.run_until_complete(self._method(*args, **kwargs))

    async def map(self, items, **kwargs):
        return await asyncio.gather(
            *[self._method(item, **kwargs) for item in items],
            return_exceptions=True
        )

    def sync_map(self, items, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.map(items, **kwargs))


make_synced = MakeSynced


def reliable_call(method):
    """Reply request if rps limit exceeded or tokens ended"""

    @wraps(method)
    async def wrapper(*args, **kwargs):
        while True:
            try:
                return await method(*args, **kwargs)
            except RpsLimitException:
                await asyncio.sleep(0.01)
                continue
            except TokenAuthFailed:
                continue
            except NoTokenAvailableException:
                # TODO Think hard
                raise

    return wrapper

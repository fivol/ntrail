import asyncio
import logging

from worker.parsers.vk.vk import VkMethods
from worker.ctx import get_context
from worker import caching

logger = logging.getLogger('engine')

parsers = [VkMethods]

ctx = get_context()


class Engine:
    """Worker engine
    All worker functionlity should be used in this context manager
    """

    _instance_count = 0

    def __init__(self, caching=True, **kwargs):
        self._instance_count += 1
        assert self._instance_count <= 1, 'Engine must be in single instance'
        self._parsers = parsers
        ctx.caching = caching
        self.__stopped = False
        for name, value in kwargs:
            setattr(ctx, name, value)

        self._init_modules()

    def __enter__(self):
        return self

    @classmethod
    def _init_modules(cls):
        logger.info('Worker engine started')
        caching.init()

    async def _stop_all(self):
        self.__stopped = True
        await asyncio.gather(
            *[cls.stop() for cls in self._parsers]
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            assert asyncio.get_running_loop()
        except RuntimeError:
            asyncio.get_event_loop().run_until_complete(
                self._stop_all()
            )
        else:
            raise EnvironmentError

    def __del__(self):
        assert self.__stopped


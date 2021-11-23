import asyncio
import logging

from worker import IGMethods
from worker.credentials.models import bind
from worker.parsers.vk.vk import VKMethods
from worker.ctx import get_context
from worker.helpers import caching

logger = logging.getLogger(__name__)

parsers = [VKMethods, IGMethods]

ctx = get_context()


class Engine:
    """Worker engine
    All worker functionlity should be used in this context manager
    """

    _instance_count = 0

    def __init__(self, caching=True, logging_disabled=False, timeout=100, **kwargs):
        self._instance_count += 1
        assert self._instance_count <= 1, 'Engine must be in single instance'
        self._parsers = parsers
        kwargs.update(caching=caching, timeout=timeout, logging_disabled=logging_disabled)
        self.__stopped = False
        for name, value in kwargs.items():
            setattr(ctx, name, value)

        self._init_modules()

    async def __aenter__(self):
        await bind()
        return self

    @classmethod
    def _init_modules(cls):
        logger.info('Worker engine started')
        caching.init()
        ctx.initialized = True
        ctx.set_default('timeout', 3)

        if ctx.get('logging_disabled'):
            logger.disabled = True

    async def stop(self):
        self.__stopped = True
        await asyncio.gather(
            *[cls.stop() for cls in self._parsers]
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    def __del__(self):
        assert self.__stopped


import asyncio

from .parsers.vk.vk import VkMethods


parsers = [VkMethods]


class Engine:
    """Worker engine
    All worker functionlity should be used in this context manager
    """

    _instance_count = 0

    def __init__(self):
        self._instance_count += 1
        assert self._instance_count <= 1, 'Engine must be in single instance'
        self._parsers = parsers
        assert parsers
        self.__stopped = False

    def __enter__(self):
        return self

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

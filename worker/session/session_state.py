import logging
from time import time
from abc import abstractmethod

logger = logging.getLogger('session')


class SessionState:
    """
    Описывает вызов токена, время обращения к нему, состояние и прочее
    """

    def __init__(self, key):
        self.session = self.create(key)
        self._key = key
        self.last_used_time = None
        # Если словил limit, это значение указывает, когда снова будет в строю (если известно)
        self.will_ready_time = None
        self.status = None
        self._expire_time = None
        self.__closed = False

    @classmethod
    @abstractmethod
    def create(cls, key):
        pass

    @abstractmethod
    async def close(self):
        pass

    async def single_close(self):
        if self.__closed:
            logger.warning(f'Closing session second time. (key: {self._key}')
            return
        self.__closed = True
        await self.close()

    @abstractmethod
    def handle_error(self, exc_type, exc_val, exc_tb):
        pass

    def is_ready(self):
        # TODO
        return not self.is_expired()

    def is_expired(self):
        return self._expire_time and time() > self._expire_time

    async def __adel__(self):
        await self.single_close()

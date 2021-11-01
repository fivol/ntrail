import logging
from time import time
from abc import abstractmethod
from collections import deque
from worker.ctx import get_context

logger = logging.getLogger('session')

ctx = get_context()


class SessionState:
    """
    Описывает вызов токена, время обращения к нему, состояние и прочее
    """

    def __init__(self, key, key_type):
        self._key_type = key_type
        self.session = self.create(key)
        self._key = key
        self.last_used_time = None
        # Если словил limit, это значение указывает, когда снова будет в строю (если известно)
        self.will_ready_time = None
        self.status = None
        self._expire_time = None
        self.__closed = False
        self.__using_times = deque()
        assert ctx.get('initialized')

    def rps(self):
        """
        Сколько запросов максимум могли сделть за предыдущую секунду
        """
        t = time()
        while self.__using_times and self.__using_times[0] + 1 < t:
            self.__using_times.popleft()

        return len(self.__using_times)

    def notify_use(self):
        """Вызывается для поддержания rps при использовании"""
        self.__using_times.append(time())

    @classmethod
    @abstractmethod
    def create(cls, key):
        pass

    def __hash__(self):
        return hash(self._key)

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


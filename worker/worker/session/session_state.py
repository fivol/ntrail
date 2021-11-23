from __future__ import annotations
import logging
from time import time
from abc import abstractmethod
from collections import deque
from pydantic import BaseModel

from worker.credentials.access import AccessModel

logger = logging.getLogger(__name__)


class UsageStat(BaseModel):
    rps: int
    delay: float
    usage_count: int = 0

    def __lt__(self, other: UsageStat):
        if self.delay >= 1 or other.delay >= 1:
            return self.delay > other.delay
        return self.rps < other.rps

    def __eq__(self, other):
        return self.rps == other.rps and self.delay == other.delay

    def __hash__(self):
        return hash(self.rps) + hash(self.delay)


class SessionState:
    """
    Описывает вызов токена, время обращения к нему, состояние и прочее
    """

    def __init__(self, key, key_type):
        self._key_type = key_type
        self.session = self.create(key)
        self.key = key
        self.last_used_time = None
        # Если словил limit, это значение указывает, когда снова будет в строю (если известно)
        self.will_ready_time = None
        self.status = None
        self._expire_time = None
        self.__closed = False
        self._using_times = deque()
        self._last_using = 0
        self._usage_count = 0

    def usage_stat(self) -> UsageStat:
        """
        Сколько запросов максимум могли сделть за предыдущую секунду
        """
        t = time()
        while self._using_times and self._using_times[0] + 1 < t:
            self._using_times.popleft()

        rps = len(self._using_times)
        return UsageStat(rps=rps, delay=time() - self._last_using, usage_count=self._usage_count)

    def notify_use(self):
        """Вызывается для поддержания rps при взятии из хранилища"""
        self._using_times.append(time())
        self._usage_count += 1

    def notify_return(self):
        """Выхывается по возвращении в хранлище (SessionManager)"""
        self._last_using = time()

    @classmethod
    @abstractmethod
    def create(cls, access: AccessModel):
        pass

    def __hash__(self):
        return hash(self.key)

    @abstractmethod
    async def close(self):
        pass

    async def single_close(self):
        if self.__closed:
            logger.warning(f'Closing session second time. (key: {self.key}')
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


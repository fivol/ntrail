from __future__ import annotations
from functools import total_ordering
from time import time
from abc import abstractmethod
from collections import deque
from pydantic import BaseModel
from loguru import logger

from worker.credentials.access import AccessModel


@total_ordering
class UsageStat(BaseModel):
    rps: int
    last_usage: float
    usage_count: int = 0
    in_use: bool = False

    def delay(self):
        return time() - self.last_usage

    def __lt__(self, other: UsageStat):
        if self.rps > 1 and other.rps > 1:
            return self.rps < other.rps
        return self.last_usage < other.last_usage

    def __hash__(self):
        return hash(self.rps) + hash(self.last_usage) + hash(self.usage_count)


@total_ordering
class SessionState:
    """
    Описывает вызов токена, время обращения к нему, состояние и прочее
    """

    def __init__(self, key, key_type):
        self._key_type = key_type
        self.session = self.create(key)
        self.key: AccessModel = key
        self.last_used_time = None
        # Если словил limit, это значение указывает, когда снова будет в строю (если известно)
        self.will_ready_time = None
        self.status = None
        self._expire_time = None
        self.__closed = False
        self._using_times = deque()
        self._stat = UsageStat(rps=0, last_usage=0, usage_count=0)

    def usage_stat(self) -> UsageStat:
        """
        Сколько запросов максимум могли сделть за предыдущую секунду
        """
        return self._stat

    def update_rps(self):
        t = time()
        while self._using_times and self._using_times[0] + 1 < t:
            self._using_times.popleft()

        self._stat.rps = len(self._using_times)

    def notify_use(self):
        """Вызывается для поддержания rps при взятии из хранилища"""
        self._using_times.append(time())
        self.update_rps()
        self._stat.usage_count += 1
        self._stat.in_use = True

    def notify_return(self):
        """Вызывается по возвращении в хранлище (SessionManager)"""
        self._stat.last_usage = time()
        self._stat.in_use = False

    @classmethod
    @abstractmethod
    def create(cls, access: AccessModel):
        pass

    def __hash__(self):
        return hash(self.key.token)

    def __lt__(self, other: SessionState):
        # return hash(self) < hash(other)
        return (self._stat, hash(self)) < (other._stat, hash(other))

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

    def __repr__(self):
        return f'SessionState(hash: {hash(self)})'


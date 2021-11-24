import logging
import random
from sortedcontainers import SortedSet

from worker.credentials.db import AccessStatus
from worker.session.exceptions import NoTokenAvailableException, RpsLimitException, SessionAction, SessionRemove
from worker.session.session_provider import SessionProvider
from worker.session.session_state import SessionState, UsageStat

from worker.credentials.credentials import Credentials
from worker.credentials.access import AccessModel

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Поддерживает сессии,
    Возвращает алгоритмом round robin
    """

    def __init__(self, key_type: str, controller: type(SessionState), max_rps=None,
                 requests_delay_min: float = None, requests_delay_max: float = None):
        logger.info('INIT session manager')
        self._session_controller = controller

        self._all_sessions = set()
        self._active_sessions = SortedSet()
        self._waiting_queue = set()

        self._key_type = key_type
        self._max_rps = max_rps
        self._requests_delay_min = requests_delay_min
        self._requests_delay_max = requests_delay_max
        self._stop_called = False
        self._stop_access_acquiring = False

    async def get(self):
        session = await self._get_session()
        self.notify_use(session)
        return SessionProvider(session=session, manager=self)

    def notify_use(self, session: SessionState):
        self._active_sessions.remove(session)
        session.notify_use()
        self._active_sessions.add(session)

    def notify_return(self, session: SessionState):
        self._active_sessions.remove(session)
        session.notify_return()
        self._active_sessions.add(session)

    def _create_session(self, key) -> SessionState:
        return self._session_controller(key=key, key_type=self._key_type)

    # def _update_active_session(self, session: SessionState):
    #     self._active_sessions.remove(session)
    #     self._active_sessions.add(session)

    # def _check_waiting_queue(self):
    #     while self._waiting_queue:
    #         revive_time, session = self._waiting_queue.pop()
    #         if revive_time < time():
    #             self._add_active_session(session)
    #         else:
    #             self._waiting_queue.add((revive_time, session))
    #             break

    def _add_new_keys(self, models: list[AccessModel]):
        for model in models:
            session: SessionState = self._create_session(model)
            self._active_sessions.add(session)
            self._all_sessions.add(session)
            # TODO tokens can be not plain string, for example can contain revive time

    async def _receive_keys(self, count=None) -> bool:
        count = count or max(1, len(self._all_sessions))
        if self._stop_access_acquiring:
            return False
        models = await Credentials.get_access(self._key_type, count)
        logger.info('New %s access tokens (count: %s)', len(models), count)
        if len(models) < count:
            self._stop_access_acquiring = True
            logger.warning('Credentials Server give less keys then requested: %s < %s', len(models), count)
        self._add_new_keys(models)
        return bool(models)

    # async def _return_expired(self, receive=False):
    #     if receive:
    #         await self._receive_keys()

    def _can_use_session(self, stat: UsageStat):
        if not stat.usage_count:
            return True
        if self._max_rps and stat.rps >= self._max_rps:
            return False
        delay_time = self._requests_delay_min
        if self._requests_delay_min and self._requests_delay_max:
            delay_time = random.uniform(self._requests_delay_min, self._requests_delay_max)
        if delay_time and stat.delay() < delay_time:
            return False
        return True

    async def _get_session(self) -> SessionState:
        while True:
            # if not len(self._active_sessions) or not randint(0, 10):
            #     self._check_waiting_queue()
            if not self._active_sessions:
                if await self._receive_keys():
                    continue
                raise NoTokenAvailableException()
            stat, session = self._active_sessions[0]
            if not self._can_use_session(stat):
                if await self._receive_keys():
                    continue
                raise RpsLimitException()

            return session

    async def return_session(self, session: SessionState, action: SessionAction = None):
        if isinstance(action, SessionRemove):
            self._active_sessions.remove(session)
            self._all_sessions.remove(session)
            await Credentials.return_access([session.key], error=AccessStatus.denied)
            logger.error('SESSION REMOVING')

    async def stop(self):
        logger.info('STOP session manager')
        assert not self._stop_called
        self._stop_called = True
        while len(self._active_sessions):
            session = self._active_sessions.pop(0)
            await session.single_close()
        accesses = [state.key for state in self._all_sessions]
        self._all_sessions.clear()
        await Credentials.return_access(accesses)

    def __del__(self):
        # TODO make cool
        if self._all_sessions:
            assert self._stop_called, 'Must close session, may be you forgot "with Engine()" statement'

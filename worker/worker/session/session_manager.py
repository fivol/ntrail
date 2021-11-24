import asyncio
import logging
import random
from random import randint, randrange
from time import time
from sortedcontainers import SortedSet, SortedDict

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

        self._all_keys = set()
        self._all_sessions = {}
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
        return SessionProvider(session=session, manager=self)

    def _create_session(self, key) -> SessionState:
        return self._session_controller(key=key, key_type=self._key_type)

    def _add_active_session(self, session: SessionState):
        priority_session = (session.usage_stat(), session)
        self._active_sessions.add(priority_session)
        self._all_sessions[hash(session)] = priority_session

    def _check_waiting_queue(self):
        while self._waiting_queue:
            revive_time, session = self._waiting_queue.pop()
            if revive_time < time():
                self._add_active_session(session)
            else:
                self._waiting_queue.add((revive_time, session))
                break

    def __add_new_keys(self, models: list[AccessModel]):
        for model in models:
            session = self._create_session(model)
            self._all_keys.add(model)
            self._add_active_session(session)
            # TODO tokens can be not plain string, for example can contain revive time

    async def _receive_keys(self) -> bool:
        count = max(1, len(self._all_keys))
        if self._stop_access_acquiring:
            return False
        models = await Credentials.get_access(self._key_type, count)
        logger.info('New %s access tokens (count: %s)', len(models), count)
        if len(models) < count:
            self._stop_access_acquiring = True
            logger.warning('Credentials Server give less keys then requested: %s < %s', len(models), count)
        self.__add_new_keys(models)
        return bool(models)

    async def _return_expired(self, receive=False):
        if receive:
            await self._receive_keys()

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
            if not len(self._active_sessions) or not randint(0, 10):
                self._check_waiting_queue()
            if not self._active_sessions:
                if await self._receive_keys():
                    continue
                raise NoTokenAvailableException()
            stat, session = self._active_sessions.pop(0)
            self._add_active_session(session)
            if not self._can_use_session(stat):
                if await self._receive_keys():
                    continue
                raise RpsLimitException()

            return session

    async def return_session(self, session: SessionState, action: SessionAction = None):
        if isinstance(action, SessionRemove):
            if hash(session) in self._all_sessions:
                self._active_sessions.remove(self._all_sessions[hash(session)])
                del self._all_sessions[hash(session)]
                self._all_keys.remove(session.key)
                await Credentials.return_access([session.key], error=AccessStatus.denied)
                logger.error('SESSION REMOVING')
        else:
            # TODO something went wrong
            if self._all_sessions[hash(session)] in self._active_sessions:
                try:
                    self._active_sessions.remove(self._all_sessions[hash(session)])
                except ValueError:
                    pass
            self._add_active_session(session)
        # TODO handle session actions

    async def stop(self):
        logger.info('STOP session manager')
        assert not self._stop_called
        self._stop_called = True
        keys = list(self._all_keys)
        while len(self._active_sessions):
            try:
                rps, session = self._active_sessions.pop(0)
                await session.single_close()
            except (KeyError, ValueError):
                # TODO WHYYYYYY Try-except (why pop failed)
                pass
        self._all_keys.clear()
        self._active_sessions.clear()
        await Credentials.return_access(keys)

    def __del__(self):
        # TODO make cool
        if self._all_sessions:
            assert self._stop_called, 'Must close session, may be you forgot "with Engine()" statement'

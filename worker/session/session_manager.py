import asyncio
import logging
from random import randint
from time import time

from session.credentials import CredentialsServerApi
from session.exceptions import NoTokenAvailableException, RpsLimitException, SessionAction
from session.session_provider import SessionProvider
from session.session_state import SessionState

logger = logging.getLogger('session')


class SessionManager:
    """
    Поддерживает сессии,
    Возвращает алгоритмом round robin
    """

    def __init__(self, key_type: str, controller: type(SessionState), max_rps=int(1e6)):
        self._session_controller = controller

        self._all_keys = set()
        self._all_sessions = {}
        self._active_sessions = set()
        self._waiting_queue = set()

        self._key_type = key_type
        self._max_rps = max_rps
        self._stop_called = False

    def get(self):
        session = self._get_session()
        return SessionProvider(session=session, manager=self)

    def _create_session(self, key) -> SessionState:
        return self._session_controller(key=key, key_type=self._key_type)

    def _add_active_session(self, session):
        priority_session = (session.rps(), session)
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

    def __filter_new_keys(self, keys):
        new_keys = list(filter(lambda t: t not in self._all_keys, keys))
        if len(new_keys) != len(keys):
            raise RuntimeWarning('Credentials server do not work properly')
        return new_keys

    def __add_new_keys(self, keys):
        for key in keys:
            session = self._create_session(key)
            self._all_keys.add(key)
            self._add_active_session(session)
            # TODO tokens can be not plain string, for example can contain revive time

    def _receive_keys(self) -> bool:
        count = max(1, len(self._active_sessions))
        tokens = self.__filter_new_keys(CredentialsServerApi.get_keys(self._key_type, count))
        if len(tokens) < count:
            logger.warning('Credentials Server give less keys then requested: %s < %s', len(tokens), count)
        self.__add_new_keys(tokens)
        return bool(tokens)

    def _return_expired(self, receive=False):
        if receive:
            self._receive_keys()

    def _get_session(self) -> SessionState:
        while True:
            if not len(self._active_sessions) or not randint(0, 10):
                self._check_waiting_queue()

            if not self._active_sessions:
                if self._receive_keys():
                    continue
                raise NoTokenAvailableException()
            rps, session = self._active_sessions.pop()
            self._add_active_session(session)
            if session.rps() >= self._max_rps:
                if self._receive_keys():
                    continue
                raise RpsLimitException()

            return session

    def return_session(self, session, action: SessionAction = None):
        self._active_sessions.remove(self._all_sessions[hash(session)])
        self._add_active_session(session)
        # TODO handle session actions

    async def stop(self):
        self._stop_called = True
        while self._active_sessions:
            rps, session = self._active_sessions.pop()
            await session.single_close()

    def __del__(self):
        if self._all_sessions:
            assert self._stop_called, 'Must close session, may be you forgot "with Engine()" statement'

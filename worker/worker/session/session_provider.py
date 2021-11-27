import asyncio
import logging

from worker.credentials.db import AccessStatus
from worker.session.exceptions import SessionAction, SessionRemove, TokenAuthFailed
from worker.parsers.exceptions import AccessApiException, AccessUnknownBehaviorExceptions
from worker.session.session_state import SessionState

logger = logging.getLogger(__name__)


class SessionProvider:
    def __init__(self, session: SessionState, manager=None):
        self._session = session
        self._manager = manager

    async def __aenter__(self):
        return self._session.session

    async def _return_session(self):
        await self._manager.return_session(self._session)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._manager.notify_return(self._session)
        if exc_type == asyncio.CancelledError:
            await self._return_session()
            return False
        if isinstance(exc_val, AccessApiException):
            await self._return_session()
            return False
        if isinstance(exc_val, AccessUnknownBehaviorExceptions):
            await self._manager.return_session(self._session, action=SessionRemove(AccessStatus.unknown_error))
            return False
        if exc_type:
            try:
                self._session.handle_error(exc_type, exc_val, exc_tb)
            except SessionAction as action:
                logger.error('Receive SessionAction: %s', action)
                await self._manager.return_session(self._session, action=action)
                raise TokenAuthFailed()
            except Exception:
                await self._return_session()
                raise

        await self._return_session()
        return False

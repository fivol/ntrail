import asyncio

from worker.session.exceptions import SessionAction, SessionRemove, TokenAuthFailed
from worker.session.session_state import SessionState


class SessionProvider:
    def __init__(self, session: SessionState, manager=None):
        self._session = session
        self._manager = manager

    async def __aenter__(self):
        return self._session.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._manager.notify_return(self._session)
        if exc_type == asyncio.CancelledError:
            await self._manager.return_session(self._session)
            return False
        if exc_type:
            try:
                self._session.handle_error(exc_type, exc_val, exc_tb)
            except SessionAction as action:
                await self._manager.return_session(self._session, action=action)
                raise TokenAuthFailed()
            except Exception:
                await self._manager.return_session(self._session)
                raise

        await self._manager.return_session(self._session)
        return False

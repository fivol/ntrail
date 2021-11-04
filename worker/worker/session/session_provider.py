import asyncio

from worker.session.exceptions import SessionAction, SessionRemove


class SessionProvider:
    def __init__(self, session, manager=None):
        self._session = session
        self._manager = manager

    def __enter__(self):
        self._session.notify_use()
        return self._session.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == asyncio.CancelledError:
            return False
        if exc_type:
            try:
                self._session.handle_error(exc_type, exc_val, exc_tb)
            except SessionRemove as action:
                self._manager.return_session(self._session, action=action)
                return False
            except SessionAction:
                return False

        self._manager.return_session(self._session)
        return False

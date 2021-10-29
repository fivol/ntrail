from session.exceptions import SessionException


class SessionProvider:
    def __init__(self, session, manager=None):
        self._session = session
        self._manager = manager

    async def __aenter__(self):
        return self._session.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            self._session.handle_error(exc_type, exc_val, exc_tb)
        except SessionException as action:
            self._manager.return_session(self._session, action=action)
        else:
            self._manager.return_session(self._session)
        return False

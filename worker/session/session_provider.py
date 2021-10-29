
class SessionProvider:
    def __init__(self, session, manager=None, error_handler=None):
        self._session = session
        self._manager = manager
        self._error_handler = error_handler

    async def __aenter__(self):
        return self._session.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        action = self._error_handler(exc_type, exc_val, exc_tb)
        self._manager.return_session(self._session, action=action)
        return False

from loguru import logger

from worker.credentials.db import AccessStatus
from worker.parsers.ig.instagramscraper.instagram import Instagram
from worker.parsers.ig.instagramscraper.exceptions import *

from worker.credentials.access import AccessModel
from worker.ctx import get_context
from worker.session.exceptions import SessionRemove, SessionWait
from worker.session.session_state import SessionState
ctx = get_context()


class IgApiSession(SessionState):
    def __init__(self, *args, **kwargs):
        self.__ig_session = None
        super().__init__(*args, **kwargs)

    def create(self, access: AccessModel):
        self.__ig_session = Instagram(cookie=access.data['cookie'])
        return self.__ig_session

    async def close(self):
        pass

    def handle_error(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, InstagramSuspiciousActivity):
            raise SessionRemove(AccessStatus.suspicious_activity)
        if isinstance(exc_val, InstagramTooManyRequestsException):
            logger.error('Instagram: too many requests')
            raise SessionWait()
        if isinstance(exc_val, InstagramLoginRedirectException):
            raise SessionRemove(AccessStatus.login_redirect)
        if isinstance(exc_val, InstagramAuthException):
            raise SessionRemove(AccessStatus.auth_error)
        # TODO Think of unknown thrown exception

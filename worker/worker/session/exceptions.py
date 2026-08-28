from worker.credentials.db import AccessStatus


class SessionManagerException(Exception):
    """Can not perform query because of some troubles with session manager/provider/server etc"""
    pass


class NoTokenAvailableException(SessionManagerException):
    pass


class RpsLimitException(SessionManagerException):
    pass


class TokenAuthFailed(SessionManagerException):
    """Troubles with request execution related to token itself"""
    pass


# -----------------------------------------------------------------------------------


class SessionAction(Exception):
    """Action should be done with session"""
    pass


class SessionWait(SessionAction):
    """Need to wait (seconds) seconds before use this session next time"""

    def __init__(self, seconds: int = 10):
        self.seconds = seconds


class SessionRemove(SessionAction):
    """Can't use this session anymore, should be removed from storage. It is just rubbish"""

    def __init__(self, access_status: AccessStatus):
        self.access_status = access_status

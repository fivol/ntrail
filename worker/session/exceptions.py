class RequestException(Exception):
    pass


class NoTokenAvailableException(RequestException):
    pass


class ApiLimitException(RequestException):
    pass


class SessionException(Exception):
    pass


class SessionAction(SessionException):
    """Action should be done with session"""
    pass


class SessionWait(SessionAction):
    """Need to wait (seconds) seconds before use this session next time"""
    def __init__(self, seconds: int):
        self.seconds = seconds


class SessionRemove(SessionAction):
    """Can't use this session anymore, should be removed from storage. It is just rubbish"""
    def __init__(self, reason: str = None):
        self.reason = reason

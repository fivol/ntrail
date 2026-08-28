from worker.parsers.exceptions import AccessApiException


class InstagramException(Exception):
    """Base instagram exceptions.
    All exception raised by this lib"""
    code = 500

    def __init__(self, cookies=None, url=None, code=None, **kwargs):
        self.cookies = cookies
        self.url = url
        self._code = code

    @classmethod
    def default(cls, code=500):
        return {
            404: InstagramNotFoundException,
            400: InstagramNotFoundException,
            429: InstagramTooManyRequestsException
        }.get(code, cls)(code=code)

    def __str__(self):
        return f'InstagramException.default({self._code or self.code})'


class InstagramAuthException(InstagramException):
    """All exceptions related to account auth"""
    code = 401


class InstagramActionException(AccessApiException, InstagramException):
    """Exceptions related to users requests. Such exceptions returned to the clients"""


class InstagramLoginRedirectException(InstagramAuthException):
    pass


class InstagramSuspiciousActivity(InstagramAuthException):
    code = 501


class InstagramNotFoundException(InstagramActionException):
    code = 404


class InstagramTooManyRequestsException(InstagramActionException):
    code = 429

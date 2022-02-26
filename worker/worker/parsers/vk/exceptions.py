from enum import Enum
from typing import Optional

from aiovk.exceptions import VkAPIError

from worker.parsers.exceptions import AccessApiException


class VKErrorType(Enum):
    UNKNOWN = -1

    ACCESS_DENIED = 15
    PRIVATE_PROFILE = 30
    USER_WAS_BANNED = 37
    UNKNOWN_USER = 39
    UNKNOWN_GROUP = 40
    INVALID_USER_ID = 113
    GROUP_AUTHORIZATION_FAILED = 27


class VKError(AccessApiException):

    def __init__(self, error: VkAPIError = None, code=None, msg=None):
        self._msg = msg
        self._code = code
        self._error = error

    @property
    def code(self):
        return self._code or self._error.error_code

    @property
    def msg(self):
        return self._msg or self._error.error_msg

    @property
    def type(self):
        try:
            return VKErrorType(self.code)
        except ValueError:
            return VKErrorType(-1)

    def __str__(self):
        return f'VK API Error: ({self.code}) {self.msg}'


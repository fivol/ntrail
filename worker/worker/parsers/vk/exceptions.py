from enum import Enum

from aiovk.exceptions import VkAPIError

from worker.parsers.exceptions import ParserRealError


class VKErrorType(Enum):
    UNKNOWN = -1

    PRIVATE_PROFILE = 30
    USER_WAS_BANNED = 37
    UNKNOWN_USER = 39
    UNKNOWN_GROUP = 40


class VKError(ParserRealError):

    def __init__(self, error: VkAPIError):
        self._error = error

    @property
    def code(self):
        return self._error.error_code

    @property
    def msg(self):
        return self._error.error_msg

    @property
    def type(self):
        return VKErrorType(self.code)

    def __str__(self):
        return f'VK API Error: ({self.code}) {self.msg}'


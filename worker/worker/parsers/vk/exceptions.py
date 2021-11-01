from aiovk.exceptions import VkAPIError

from worker.parsers.exceptions import ParserRealError


class VKError(ParserRealError):

    def __init__(self, error: VkAPIError):
        self._error = error

    @property
    def code(self):
        return self._error.error_code

    @property
    def msg(self):
        return self._error.error_msg

    def __str__(self):
        return f'VK API Error: ({self.code}) {self.msg}'

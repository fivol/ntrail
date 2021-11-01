from aiovk.exceptions import VkAPIError


class VKError(Exception):

    def __init__(self, error: VkAPIError):
        self._error = error

    def code(self):
        return self._error.error_code

    def msg(self):
        return self._error.error_msg

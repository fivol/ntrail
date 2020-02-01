VK_API_UNKNOWN_ERROR = 1
UNKNOWN_ERROR = -1
REQUEST_EXECUTE_ERROR = 0
ACCESS_DENIED_ERROR = 15
PRIVATE_PROFILE_ERROR = 30
INVALID_ID_ERROR = 113
ALBUM_ACCESS_DENIED_ERROR = 200


class APIError:
    errors = None
    request_result_errors = None
    service = None

    def __new__(cls, obj):
        if isinstance(obj, APIError):
            return obj
        elif isinstance(obj, dict):
            assert obj['status'] == 'error'
            return object.__new__(services[obj['service']])
        elif isinstance(obj, int):
            return object.__new__(cls)
        else:
            raise TypeError('API ERROR wrong init type')

    def __init__(self, obj):
        assert self.__class__ != APIError
        if isinstance(obj, int):
            self.code = obj
        elif isinstance(obj, dict):
            assert obj['status'] == 'error'
            self.code = obj['code']

    def __repr__(self):
        return f'{self.errors[self.code]}. Error {self.service} code {self.code}'

    def to_dict(self):
        return {
            'status': 'error',
            'service': self.service,
            'code': self.code,
        }

    @classmethod
    def is_error(cls, obj_dict):
        return (isinstance(obj_dict, dict) and obj_dict.get('status') == 'error') or isinstance(obj_dict, APIError)

    @property
    def description(self):
        return self.errors[self.code][1]

    def is_request_result(self):
        return self.code in self.request_result_errors


class ServerError(APIError):
    errors = {
        REQUEST_EXECUTE_ERROR: 'Fail to execute request. Catch unexpected error'
    }
    request_result_errors = {}
    service = 'server'


class VKError(APIError):
    errors = {
        UNKNOWN_ERROR: 'Unknown error code from vk api',
        VK_API_UNKNOWN_ERROR: 'Unknown error occurred on vk servers',
        ACCESS_DENIED_ERROR: 'Access denied: this content is private',
        PRIVATE_PROFILE_ERROR: 'This profile is private',
        INVALID_ID_ERROR: 'Invalid input data: object does not exist',
        ALBUM_ACCESS_DENIED_ERROR: 'Access denied to this album'
    }
    request_result_errors = {ACCESS_DENIED_ERROR,
                             PRIVATE_PROFILE_ERROR,
                             INVALID_ID_ERROR}
    service = 'vk'


services = {
    'vk': VKError,
    'server': ServerError
}

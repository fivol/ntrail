VK_API_UNKNOWN_ERROR = 1
UNKNOWN_ERROR = -1
REQUEST_EXECUTE_ERROR = 0
ACCESS_DENIED_ERROR = 15
PRIVATE_PROFILE_ERROR = 30
INVALID_ID_ERROR = 113
ALBUM_ACCESS_DENIED_ERROR = 200
USER_AUTHORIZATION_ERROR = 5


class VKError(APIError):
    errors = {
        UNKNOWN_ERROR: 'Unknown error code from vk api',
        VK_API_UNKNOWN_ERROR: 'Unknown error occurred on vk servers',
        ACCESS_DENIED_ERROR: 'Access denied: this content is private',
        PRIVATE_PROFILE_ERROR: 'This profile is private',
        INVALID_ID_ERROR: 'Invalid input data: object does not exist',
        ALBUM_ACCESS_DENIED_ERROR: 'Access denied to this album',
        USER_AUTHORIZATION_ERROR: 'Авторизация пользователя не удалась. Убедитесь, что Вы используете верную схему авторизации'
    }
    request_result_errors = {ACCESS_DENIED_ERROR,
                             PRIVATE_PROFILE_ERROR,
                             INVALID_ID_ERROR}
    service = 'vk'


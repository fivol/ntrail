
class ApiBaseException(Exception):
    pass


class WrongInputError(ApiBaseException):
    pass


class ServerError(ApiBaseException):
    pass

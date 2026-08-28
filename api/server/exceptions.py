
class NtrailBaseException(Exception):
    pass


class NtrailWrongInputError(NtrailBaseException):
    pass


class NtrailServerError(NtrailBaseException):
    pass

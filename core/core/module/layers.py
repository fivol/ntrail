from functools import wraps

from core.config import logger


def public_object_method(method):
    """Method valid and public"""
    @wraps(method)
    def wrapper(obj, *args, **kwargs):
        if not obj.valid:
            logger.warning("This object isn't accessible (maybe private), %s.%s",
                           obj.__class__.__name__, method.__name__)
            raise
        return method(obj, *args, **kwargs)

    return wrapper


def valid_object_method(method):
    @wraps(method)
    def wrapper(obj, *args, **kwargs):
        if not obj.valid:
            logger.warning("This object isn't valid! -> method %s in class %s can't be used.",
                           obj.__class__.__name__, method.__name__)
            return None
        return method(obj, *args, **kwargs)
    return wrapper

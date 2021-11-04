from functools import wraps

from core.config import logger


def public_object_method(method):
    """Method valid and public"""
    @wraps(method)
    async def wrapper(obj, *args, **kwargs):
        if not await obj.valid():
            logger.warning("This object isn't accessible (maybe private), %s.%s",
                           obj.__class__.__name__, method.__name__)
            raise AssertionError('Object is not public')
        return await method(obj, *args, **kwargs)

    return wrapper


def valid_object_method(method):
    @wraps(method)
    async def wrapper(obj, *args, **kwargs):
        if not obj.valid:
            logger.warning("This object isn't valid! -> method %s in class %s can't be used.",
                           obj.__class__.__name__, method.__name__)
            raise AssertionError('Object is not valid')
        return await method(obj, *args, **kwargs)
    return wrapper

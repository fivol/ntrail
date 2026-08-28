from functools import wraps

from core.helpers.utils import init_object_props
from pycommon.decors import cache_method_ignore_args


def data_method_decorator(method):
    @cache_method_ignore_args
    @wraps(method)
    async def wrapper(self):
        result = await method(self)
        init_object_props(self, result)
        return result
    return wrapper

from functools import wraps


def cache_method_ignore_args(method):
    """
    if self._data exists -> self._data returns,
    else result caches in self._data

    def data(self):
        return 123
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        cache_field = f'_{method.__name__}'
        if hasattr(self, cache_field):
            return getattr(self, cache_field)
        method_result = method(self, *args, **kwargs)
        setattr(self, cache_field, method_result)
        return method_result

    return wrapper


import inspect
import random
from time import sleep


def split_list(list_object, segment_size):
    result_list = []
    for i in range(len(list_object) // segment_size + 1):
        begin = i * segment_size
        end = (i + 1) * segment_size
        if begin < len(list_object):
            result_list.append(list_object[begin:end])
    return result_list


def sequential_start(func):
    def wrapper(*args, **kwargs):
        global execution_locked_func
        name = func.__name__
        sum_time = 0
        while execution_locked_func.get(name, False):
            wait_time = 0.01 + random.random() / 3
            sum_time += wait_time
            sleep(wait_time)
        execution_locked_func[name] = True
        result = func(*args, **kwargs)
        execution_locked_func[name] = False
        return result

    return wrapper


def inject_methods_wrapper(wrapper_name):
    def cls_wrapper(cls):
        wrapper = getattr(cls, wrapper_name)
        for item in cls.__dict__:
            if item.startswith('_'):
                continue
            # TODO Skip all items, that is not methods
            method = getattr(cls, item)
            if not inspect.ismethod(method):
                continue

            class MethodWrapper:
                def __init__(self, _method, _wrapper):
                    self._method = _method
                    self._wrapper = _wrapper

                async def __call__(self, *args, **kwargs):
                    return await self._wrapper(self._method, args, kwargs)

            setattr(cls, item, MethodWrapper(method, wrapper))
        return cls

    return cls_wrapper

import asyncio
import inspect
import random
import typing
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


class MethodWrapper:
    def __init__(self, _method, _wrapper):
        self._method = _method
        self._wrapper = _wrapper

    async def __call__(self, *args, **kwargs):
        return await self._wrapper(self._method, args, kwargs)


class MakeSynced:
    """
    Wraps method and give .sync interface to call async functions

    --------------------
    Async variant:

        async def abc(x):
            return x
        print(asyncio.run(abs()))
    --------------------
    Sync variant:

        @MakeSynced
        async def abc(x):
            return x

        print(abc.sync(3))
    """

    def __init__(self, _method):
        self._method = _method

    async def __call__(self, *args, **kwargs):
        return await self._method(*args, **kwargs)

    def sync(self, *args, **kwargs):
        return asyncio.run(self._method(*args, **kwargs))


def inject_methods_wrappers(*wrappers):
    """
    It is decorator
    Makes decorators to all methods in class
    """
    def cls_wrapper(cls):
        wrappers_funcs = []
        for wrapper in wrappers:
            if isinstance(wrapper, str):
                wrapper_method = getattr(cls, wrapper)
                wrapper = lambda func: MethodWrapper(func, wrapper_method)

            wrappers_funcs.append(wrapper)

        for item in cls.__dict__:
            if item.startswith('_'):
                continue
            # TODO Skip all items, that is not methods
            method = getattr(cls, item)
            if not inspect.ismethod(method):
                continue

            for wrapper in wrappers_funcs:
                method = wrapper(method)

            setattr(cls, item, method)
        return cls

    return cls_wrapper


if __name__ == '__main__':
    @inject_methods_wrappers('_wrapper', MakeSynced)
    class A:
        @classmethod
        async def _wrapper(cls, method, args, kwargs):
            print('wrapper')
            return await method(*args, **kwargs)

        @classmethod
        async def a(cls, x):
            print('method a')
            return x

        @classmethod
        async def b(cls, x):
            print('method b')
            return x
    print(asyncio.run(A.a(4)))
    print(asyncio.run(A.b(3)))
    print(asyncio.run(A.a(2)))

    print(A.a.sync(2))
    print(A.b.sync(10))

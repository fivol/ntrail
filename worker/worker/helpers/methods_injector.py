import asyncio
import inspect

from worker.parsers.exceptions import AccessApiException


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
        loop = asyncio.get_event_loop()
        try:
            return loop.run_until_complete(self._method(*args, **kwargs))
        except AccessApiException as e:
            return e

    async def map(self, items, **kwargs):
        return await asyncio.gather(
            *[self._method(item, **kwargs) for item in items],
            return_exceptions=True
        )

    def sync_map(self, items, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.map(items, **kwargs))


def inject_methods_wrappers(*wrappers):
    """
    It is decorator.
    Makes decorators to all methods in class
    Ignores only
        - Fields (not executable methods)
        - Methods starting with _
        - Methods with @ignore_injection decorator
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
            if getattr(method, '_ignore_injection', False) is True:
                continue

            for wrapper in wrappers_funcs:
                name = method.__name__
                method = wrapper(method)
                method.__name__ = name

            setattr(cls, item, method)
        return cls

    return cls_wrapper


def ignore_injection(method):
    method._ignore_injection = True
    return method

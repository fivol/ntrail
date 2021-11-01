import asyncio
import inspect


class MethodWrapper:
    def __init__(self, _method, _wrapper):
        self._method = _method
        self._wrapper = _wrapper

    async def __call__(self, *args, **kwargs):
        return await self._wrapper(self._method, args, kwargs)


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

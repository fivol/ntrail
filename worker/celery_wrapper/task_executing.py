import typing
from celery_wrapper.actual_task import ActualTask


def deferred_task(func) -> typing.Callable:
    return ActualTask(func, func.__name__, func.__class__)


class TasksExecutorMeta(type):
    def __init__(cls, name, bases, dct):
        if not bases:
            # Base class creation
            pass
        else:
            for method_name in dct:
                if method_name.startswith('_'):
                    continue
                task = ActualTask(method=getattr(cls, method_name), method_name=method_name, cls=cls)
                setattr(cls, method_name, task)

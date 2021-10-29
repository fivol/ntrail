import typing
from celery import Task

from celery_wrapper.actual_task import ActualTask


class TaskBase(Task):
    def __init__(self, method: typing.Callable, method_name: str):
        self.method = method
        self.method_name = method_name

    def run(self, *args, **kwargs):
        return self.method(*args, **kwargs)


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

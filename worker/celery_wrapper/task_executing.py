import typing
from celery import Task

from celery_wrapper.actual_task import ActualTask


class TaskBase(Task):
    """
        Task class for celery, runs target method
    """

    """
    class MyMethods(...):
        @classmethod
        def _wrapper(task, method, args, kwargs):
            try:
                return method(*args, **kwargs)
            except:
                return None
            
        @classmethod
        def get_records(cls, id):
            raise Exception()
    
    """
    TASK_WRAPPER_NAME = '_wrapper'

    def __init__(self, method: typing.Callable, method_name: str, cls=None):
        self.method = method
        self._cls = cls
        self.method_name = method_name
        self._method_wrapper = self._get_cls_wrapper()

    @classmethod
    def __default_wrapper(cls, method, args, kwargs,  *_, **__):
        return method(*args, **kwargs)

    def _get_cls_wrapper(self):
        return getattr(self._cls, self.TASK_WRAPPER_NAME, self.__default_wrapper)

    def run(self, *args, **kwargs):
        return self._method_wrapper(self.method, args, kwargs, task=self)


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

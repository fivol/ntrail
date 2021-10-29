import typing
from celery import Task

from app import app


class TaskBase(Task):
    def __init__(self, method: typing.Callable, method_name: str):
        self.method = method
        self.method_name = method_name

    def run(self, *args, **kwargs):
        return self.method(*args, **kwargs)


class ActualTask:
    def __init__(self, method: typing.Callable, method_name: str, cls: type):
        """
        Вызывается в момент создания класса (прям там, где он в коде описан),
        заменяя оригинальный метод на инстанс этого класса
        :executor: настоящий метод класса, который был вызван, оборачивается
        в @classmethod для удобства использования
        """
        self.method = method
        self.method_name = method_name
        self.cls = cls
        self._celery_task = None
        self._init_task()

    def _init_task(self):
        name = f'task-{self.cls.__name__}.{self.method_name}'
        self._celery_task = TaskBase(self.method, self.method_name)
        self._celery_task.name = name
        app.register_task(self._celery_task)

    def __call__(self, *args, **kwargs):
        """
        Вызывается в момент вызова самого оригинального метода класса
        VkApi.resolve("https://vk.com/keklol")
        """
        future = self._run_task(args, kwargs)
        result = future.get(timeout=10)
        return result

    def _run_task(self, args, kwargs):
        return self._celery_task.apply_async(args, kwargs)

    def map(self, items: typing.Iterable[typing.Union[object, typing.Tuple[list, dict], dict]]):
        """
        Принимает Iterable объект и возвращает список результатов
        Ассинхронно запускает все в очередь и ждет результатов
        VkApi.friends.map([123,214,2,5,34,534,6,45,66,467,567,5,3])
        """
        class ItemParser:
            def __init__(self, item):
                self.args = ()
                self.kwargs = {}

                if hasattr(item, '__len__') \
                        and len(item) == 2 \
                        and isinstance(item[0], list)\
                        and isinstance(item[1], dict):
                    self.args = item[0]
                    self.kwargs = item[1]
                elif isinstance(item, dict):
                    self.kwargs = item
                elif isinstance(item, typing.Iterable):
                    self.args = list(item)
                else:
                    self.args = (item, )

        items = map(ItemParser, items)
        futures = list(map(lambda item: self._run_task(item.args, item.kwargs), items))
        return [future.get() for future in futures]


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

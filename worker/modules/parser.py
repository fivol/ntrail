from celery_wrapper.task_executing import TasksExecutorMeta
from session.exceptions import SessionException
from celery import Task


class BaseParser(metaclass=TasksExecutorMeta):
    """
    Базовый класс для парсеров.
    Парсеры это просто группа методов взаимодейсвия с одним сервисом,
    например с апи вк или инстаграма.
    Парсер может относиться к определенному сайту или интернету в целом.
    Парсер может реализовывать высокоуровневые методы, которые исполняются
    посредством создания ряда дополнительных задач
    """
    @classmethod
    async def _wrapper(cls, method, args, kwargs, *_, task: Task = None, **__):
        """
        Calling every time when call any method of child classes
        """
        try:
            return method(*args, **kwargs)
        except SessionException:
            # Не удалось выполнить задачу из-за проблем с сессией, первый запрос провалился
            return task.replace(task.signature(args, kwargs))

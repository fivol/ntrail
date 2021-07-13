import pickle
import random
from threading import Thread
from time import sleep, time
from .config import logger


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


class ThreadResult:
    def __init__(self, target=None, args=None, kwargs=None):
        self.result = None
        if not args:
            args = []
        if not kwargs:
            kwargs = {}

        def saver_func(*args_, **kwargs_):
            self.result = target(*args_, **kwargs_)

        self.thread = Thread(target=saver_func, args=args, kwargs=kwargs)
        self.thread.start()

    def execute(self):
        self.thread.join()
        return self.result


class MemoryCache:
    stored_data = {}
    last_save_time = 0
    get_data_locked = False

    @classmethod
    def get(cls, name, save=False):
        while cls.get_data_locked:
            sleep(0.05)
        if time() - cls.last_save_time > 3 or save:
            cls.save_memory()
        default = {}
        if name not in cls.stored_data:
            cls.stored_data[name] = default

        return cls.stored_data[name]

    @classmethod
    def save_memory(cls):
        cls.get_data_locked = True
        try:
            with open('.cache', 'wb') as f:
                pickle.dump(cls.stored_data, f)
        except:
            logger.exception('Fail to save memory')

        cls.last_save_time = time()
        cls.get_data_locked = False

    @classmethod
    def load_memory(cls):
        import pickle
        try:
            with open('.cache', 'rb') as f:
                cls.stored_data = pickle.load(f)
        except FileNotFoundError:
            logger.warning('Memory file not found!')
            cls.save_memory()

    @classmethod
    def clear_memory(cls):
        cls.stored_data.clear()
        cls.save_memory()

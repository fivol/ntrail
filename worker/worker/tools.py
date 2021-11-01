import asyncio
import logging
import random
import traceback
from functools import wraps
from time import sleep


logger = logging.getLogger('tools')


def split_list(list_object, segment_size):
    result_list = []
    for i in range(len(list_object) // segment_size + 1):
        begin = i * segment_size
        end = (i + 1) * segment_size
        if begin < len(list_object):
            result_list.append(list_object[begin:end])
    return result_list


_imported_files = set()


def assert_imported_once():
    filename = traceback.extract_stack()[-2][0]
    assert filename not in _imported_files, 'This file was already imported'
    _imported_files.add(filename)


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


def partition_split(segment_size):
    """
    Assumes first argument of method is big list,
    splits it to several smaller lists of segment_size and calls this method again
    """
    def decorator(method):
        @wraps(method)
        async def wrapper(cls, items, **kwargs):
            assert isinstance(items, list)
            if len(items) <= segment_size:
                return await method(cls, items, **kwargs)
            items_parts = split_list(items, segment_size=segment_size)
            logger.debug('Split query into %s parts', len(items_parts))
            results_parts = await asyncio.gather(*[
                method(cls, partition, **kwargs) for partition in items_parts
            ])
            assert isinstance(results_parts[0], list)
            return sum(results_parts, [])
        return wrapper
    return decorator



import random
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

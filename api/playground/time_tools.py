from contextlib import contextmanager
from time import time


@contextmanager
def print_time() -> float:
    begin = time()
    yield
    print(round(time() - begin, 4))

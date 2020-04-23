import sys
from collections import Iterable
from collections.abc import Callable
import logging
import types
from time import time


class FuncCall:
    def __init__(self, func, t0, t1, res, error, children=None):
        self.func_name = func.__name__
        self.t0 = t0
        self.t1 = t1
        self.duration = t1 - t0
        self.res = res
        self.error = error
        self.children = children or []
        self.self_duration = self.duration - sum(map(lambda x: x.duration, self.children))

    def __repr__(self):
        max_len = 50

        def repr_duration(value):
            if not value:
                return 0
            return round(value, 3)

        def repr_res(value):

            def repr_iterable(item):
                items = list(item)
                res = item.__class__.__name__ + ': '
                res += ', '.join(map(lambda x: str(x), items))
                if len(items) > max_len:
                    res += '...'
                return res

            if isinstance(value, float):
                return round(value, 2)
            value = str(value)
            return value[:max_len] + ('...' if len(value) > max_len else '')

        s = f'{self.func_name} [{repr_duration(self.duration)}'
        if self.duration != self.self_duration:
            s += f' : {repr_duration(self.self_duration)}]'
        else:
            s += ']'

        if not(self.res is None):
            s += f' -> {repr_res(self.res)}'

        return s


class VisualLogger:
    def __init__(self, online=False, min_duration_time=None, logger=None, file=None):
        if logger is None:
            logger = logging.getLogger('VisualLogging' + str(time()))
            logger.setLevel(logging.INFO)
            if not file:
                handler = logging.StreamHandler()
            else:
                handler = logging.FileHandler(file)

            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            self.logger = logger
        else:
            self.logger = logger

        self.min_duration_time = min_duration_time
        self.online = online
        self._globals_calls = []
        self._all_calls = []
        self._calls_start_time_stack = []

    def _print_call(self, call, level):
        level_string = (level * '  *').strip('*')
        self.logger.info(level_string + str(call))

    def online_call_iteration(self, call):
        if self.min_duration_time is None or call.duration >= self.min_duration_time:
            self._print_call(call, len(self._calls_start_time_stack) - 1)

        while self._calls_start_time_stack and call.t0 <= self._calls_start_time_stack[-1]:
            self._calls_start_time_stack.pop()

    def print_all_calls(self):
        stack = []
        for call in sorted(self._all_calls, key=lambda x: x.t0):
            while stack and call.t0 >= stack[-1]:
                stack.pop()

            self._print_call(call, len(stack))
            stack.append(call.t1)

    def calls(self):
        return sorted(self._globals_calls, key=lambda x: x.t0)

    def func_wrapper(self, func, base_object=None):
        assert isinstance(func, types.FunctionType)

        def wrapper(*args, **kwargs):
            t0 = time()
            error = None
            res = None
            self._calls_start_time_stack.append(t0)
            try:
                res = func(*args, **kwargs)
            except Exception as e:
                error = e
            t1 = time()
            children_calls = []

            while self._globals_calls and self._globals_calls[-1].t0 > t0:
                children_calls.append(self._globals_calls.pop())

            call_obj = FuncCall(func, t0, t1, res, error, children=children_calls[::-1])
            self._globals_calls.append(call_obj)
            self._all_calls.append(call_obj)

            if self.online:
                self.online_call_iteration(call_obj)

            if error:
                raise error

            return res

        if not base_object:
            base_object = func

        wrapper.base_object = base_object
        return wrapper

    def logit(self, obj):
        if isinstance(obj, types.FunctionType):
            return self.func_wrapper(obj)

        elif isinstance(obj, type):
            for name, attr in obj.__dict__.items():
                if not name.startswith('__') and isinstance(attr, types.FunctionType):
                    setattr(obj, name, self.func_wrapper(attr, base_object=obj))

            return obj

        else:
            raise TypeError('This type of logging objects does not supported')

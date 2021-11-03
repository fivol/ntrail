from functools import wraps


def cache_method(func):
    @wraps(func)
    def wrapper(class_obj):
        func_name = func.__name__
        class_value_name = f'{func_name}_'
        if hasattr(class_obj, class_value_name):
            return getattr(class_obj, class_value_name)
        method_result = func(class_obj)
        setattr(class_obj, class_value_name, method_result)
        return method_result

    return wrapper


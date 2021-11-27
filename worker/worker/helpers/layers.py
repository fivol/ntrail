import inspect
import logging
from functools import wraps


def method_logger(level: int = logging.DEBUG, name='', enabled=True, only_errors=False):
    """Decorator to method or function. Prints arguments and results"""
    logger = logging.getLogger(name)

    def decorator(method):
        def repr_args(args, kwargs) -> str:
            def repr_value(value):
                if inspect.isclass(value):
                    return 'cls'
                return str(value)

            kwargs = ', '.join([f'{key}={repr_value(value)}' for key, value in kwargs.items()])
            args = ', '.join(map(repr_value, args))
            return ', '.join(filter(bool, [args, kwargs]))

        def repr_result(result):
            if result is None:
                return 'None'

            def shorty(text: str, size):
                if len(text) <= size:
                    return text
                return f'{text[:size]}...'

            s = str(result)
            response_str = shorty(s, 50)
            description = f'{type(result).__name__}<size: {len(result)} bytes: {len(s)}>' if len(
                response_str) > 50 else ''
            return f'{description} {response_str}'

        @wraps(method)
        async def wrapper(*args, **kwargs):
            if not enabled:
                return await method(*args, **kwargs)
            try:
                result = await method(*args, **kwargs)
                if not only_errors:
                    logger.log(level, '%s(%s) -> %s', method.__name__, repr_args(args, kwargs), repr_result(result))
                return result
            except Exception as e:
                logger.log(level, '%s(%s) -> %s', method.__name__, repr_args(args, kwargs), str(e))
                raise

        return wrapper

    return decorator

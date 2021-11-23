from functools import wraps

from worker.parsers.utils import ListWithCount


def items_getter(method):
    @wraps(method)
    async def wrapper(*args, **kwargs):
        result = await method(*args, **kwargs)
        if kwargs.get('raw_') and isinstance(result, dict):
            return result
        items = ListWithCount(result.get('items'))
        items.count_ = result.get('count')
        return items

    return wrapper


import asyncio
import logging
from functools import wraps

from worker.tools import split_list


logger = logging.getLogger('vk-layer')


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


# TODO Make this decorator after all others in class (not it is before others)
def count_offset_iterator(max_count):
    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            count = kwargs.pop('count', max_count)
            if count <= max_count:
                return await method(*args, count=count, **kwargs)
            curr_offset = kwargs.pop('offset', 0)
            tasks = []
            while count > 0:
                curr_count = min(count, max_count)
                tasks.append(method(*args, offset=curr_offset, count=curr_count))
                curr_offset += curr_count
                count -= curr_count
            result = await asyncio.gather(*tasks)
            return sum(result, ListWithCount())
        return wrapper
    return decorator


class ListWithCount(list):
    count_ = None

    def __add__(self, other):
        result = ListWithCount(super().__add__(other))
        result.count_ = self.count_ or getattr(other, 'count_')
        return result


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

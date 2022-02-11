import asyncio
import logging
import time
from functools import wraps

from worker.parsers.utils import RichList
from worker.helpers.tools import split_list

logger = logging.getLogger()


def partition_split(segment_size):
    """
    Assumes first argument of method is big list,
    splits it to several smaller lists of segment_size and calls this method again
    If input list is empty returns empty without making queries
    """

    def decorator(method):
        @wraps(method)
        async def wrapper(cls, items, **kwargs):
            assert isinstance(items, list)
            if not items:
                return []
            if len(items) <= segment_size:
                return await method(cls, items, **kwargs)
            items_parts = split_list(items, segment_size=segment_size)
            logger.debug('Split query into {} parts', len(items_parts))
            results_parts = await asyncio.gather(*[
                method(cls, partition, **kwargs) for partition in items_parts
            ])
            assert isinstance(results_parts[0], list)
            results = sum(results_parts, [])
            return results

        return wrapper

    return decorator


# TODO Make this decorator after all others in class (not it is before others)
def count_offset_iterator(max_count):
    """If passed too big "count", splits to several method calls
        Argument "percent_" can be passed with [0, 1] diapason to load part from full count
    """

    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            count = kwargs.pop('count', max_count) or max_count
            percent_ = kwargs.pop('percent_', None)
            all_ = kwargs.pop('all_', None)
            if all_:
                percent_ = 1

            if not percent_ and count <= max_count:
                return await method(*args, count=count, **kwargs)
            curr_offset = kwargs.pop('offset', 0)
            tasks = []
            first_call = []
            while count > 0:
                curr_count = min(count, max_count)
                if percent_:
                    first_call = await method(*args, **kwargs, offset=curr_offset, count=curr_count)
                    full_count = first_call.count_
                    count = int(full_count * percent_)
                    percent_ = None
                else:
                    tasks.append(method(*args, offset=curr_offset, count=curr_count))
                curr_offset += curr_count
                count -= curr_count
            result = await asyncio.gather(*tasks)
            return first_call + sum(result, RichList())

        return wrapper

    return decorator

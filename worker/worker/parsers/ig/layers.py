import logging
from functools import wraps

from worker.parsers.utils import RichList


logger = logging.getLogger(__name__)


def paging_iterator(max_count: int):
    """Only after layer items_getter
    Receive count, percent_ and all_ parameters
    """

    def decorator(method):
        async def wrapper(cls, *args, **kwargs):
            all_items = RichList()
            count = kwargs.pop('count', max_count)
            percent_ = kwargs.pop('percent_', None)
            all_ = kwargs.pop('all_', None)
            end_cursor = kwargs.get('end_cursor', '')
            if all_:
                percent_ = 1
            while len(all_items) < count:
                items: RichList = await method(cls, *args, **kwargs,
                                               count=min(count - len(all_items), max_count) + 1,
                                               end_cursor=end_cursor)
                all_items = all_items + items
                logger.info('New items part (%s)', len(items))
                end_cursor = items.data['end_cursor']
                has_next_page = items.data['has_next_page']
                if not has_next_page:
                    break
                if percent_:
                    count = int(all_items.count_ * percent_)
            return all_items

        return wrapper

    return decorator

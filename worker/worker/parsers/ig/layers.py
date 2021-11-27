import logging

from worker.parsers.exceptions import AccessUnknownBehaviorExceptions
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
            end_cursor = kwargs.pop('end_cursor', '')
            if all_:
                percent_ = 1
            while len(all_items) < count:
                items: RichList = await method(cls, *args, **kwargs,
                                               count=max_count,
                                               end_cursor=end_cursor)
                all_items = all_items + items
                logger.info('New items part (%s)', len(items))
                end_cursor = items.data['end_cursor']
                has_next_page = items.data['has_next_page']
                if all_items.count_:
                    count = min(count, all_items.count_)
                if not has_next_page:
                    break
                if items.count_ and not len(items):
                    logger.warning('IG request return empty result, requested %s items with method %s by %s', max_count,
                                   method.__name__, args)
                    # TODO Think Hard
                    break
                if percent_:
                    count = int(all_items.count_ * percent_)

            if all_items.count_ >= count > len(all_items):
                logger.warning('Instagram return less when requests %s < %s (%s)', len(all_items), count, args)
            return all_items[:count]

        return wrapper

    return decorator

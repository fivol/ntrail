from .instagramlib import Account, WebAgentAccount, HasMediaElement
from worker.config import logger

from .state import REQUEST_ERROR_404

dead_agents = set()

try:
    with open('dead_agents', 'r') as f:
        globals()['dead_agents'] = set(f.read().split(','))
except FileNotFoundError:
    logger.debug('dead_agents file not found')
    with open('dead_agents', 'w') as f:
        f.write('')


class IGMethods:

    def repeat_load(self, func_name, count, data=None):
        assert isinstance(func_name, str)
        default_limit = 100
        limit = data.get('limit', default_limit)
        data['limit'] = limit
        data['count'] = limit
        if count < -1 or count == 0:
            raise ValueError('Wrong count value')
        result = self.make_request(func_name, **data)
        if not result:
            return None
        if result is REQUEST_ERROR_404:
            logger.warning('Repeat load func: %s, data: %s 404 ERROR', func_name, data)
            return []
        try:
            items, pointer = result
            count -= limit
        except ValueError:
            logger.error('Too many values to unpack. First request: %s', result)
            return []
        while pointer and (count == -1 or count > 0):
            result = self.make_request(func_name,
                                       **data,
                                       pointer=pointer)
            try:
                items_, pointer = result
                count -= len(items_)
                items += items_
            except ValueError:
                logger.error('Too many values to unpack: %s', result)

        return items

    def get_media(self, obj, full=False):
        assert isinstance(obj, HasMediaElement)
        element = (str(obj), full)
        full_element = (str(obj), True)
        if self.force_requests or \
                (element not in get('obj_media') and
                 full_element not in get('obj_media')):
            response = self.make_request('get_media', obj)
            if response is REQUEST_ERROR_404:
                get('obj_media')[element] = None
            else:
                get('obj_media')[element] = obj
        if element in get('obj_media'):
            return get('obj_media')[element]
        return get('obj_media')[full_element]

    def get_followers(self, username, count=-1, **kwargs):
        data = {
            'account': Account(username),
            **kwargs
        }
        nodes = self.repeat_load('get_followers', count, data=data)
        return [node.username for node in nodes]

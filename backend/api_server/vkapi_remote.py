import vk
from vk.exceptions import VkAPIError
import time
import math
from glbal import logger
import os
from tools import get
from constants import INVALID_USER_ID, ACCESS_DENIED

# vk app client_id 7091370
# service vk app key 7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1
# my user access_token 5bfaab47e81d46f1a1484571b5116939a4b142eb3253b715fa6af897018fd6662e7c41ada3ac04a63ed61
# vk error codes:
# 6 - too many requests per second;
# 30 - private user
# 15 - user deactivated


class API(vk.API):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method1 = None
        self.method2 = None
        self.kwargs = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        logger.debug('* vk api request: %s', self.method1)
        return self.make_request()

    def __getattr__(self, method_name):
        if not self.method1:
            self.method1 = method_name
        else:
            self.method2 = method_name
        return self

    def make_request(self, begin_time=None):
        wait_seconds = 1
        if not begin_time:
            begin_time = time.time()
        try:
            res = super().__getattr__(self.method1)
            if self.method2:
                res = getattr(res, self.method2)
            res = res(**self.kwargs)
            self.method1, self.method2, self.kwargs = None, None, None
            return res
        except VkAPIError as e:
            if e.code == 6:
                '''Too many requests'''
                if time.time() - begin_time > 3:
                    logger.warning('Requests time limit exceeded! Sleep 3 seconds')
                    time.sleep(3)
                logger.warning(f'VK API error 6. Too many requests per second. Wait {wait_seconds} seconds')
                time.sleep(wait_seconds)
                return self.make_request(begin_time)
            if e.code == 113:
                '''Invalid input data (object does not exist)'''
                logger.info('INVALID_USER_ID found')
                return INVALID_USER_ID

            if e.code == 15:
                '''Access denied: this profile is private'''
                logger.info('ACCESS_DENIED')
                return ACCESS_DENIED

            self.method1, self.method2, self.kwargs = None, None, None
            raise e


user_token = '5211d7bcf46f21eb3e2e5bd64e75fa1199968260d81e170a8d21bb70758f14a46dd160009815ed8fcf94d'
api = API(session=vk.Session(access_token=user_token), v='5.102', lang='ru', timeout=10)

app_token = '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'
api_app = API(session=vk.Session(access_token=app_token), v='5.102', lang='ru', timeout=10)


class VKAPI:

    @classmethod
    def user_full(cls, vkid):
        fields = [
            'photo_200', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
            'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
            'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
            'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
            'universities', 'verified', 'counters', 'screen_name', 'lists', 'is_closed'
        ]
        return api.users.get(user_ids=[int(vkid)], fields=fields)

    @classmethod
    def user_short(cls, vkid):
        result = api.users.get(user_ids=[int(vkid)])
        if isinstance(result, list):
            return result[0]
        return result

    @classmethod
    def resolve(cls, screen_name):
        return api_app.utils.resolveScreenName(screen_name=screen_name)

    @classmethod
    def group_full(cls, group_ids):
        fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                  'main_section', 'members_count', 'place',
                  'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                  'description', 'site', 'start_date']

        return api.groups.getById(group_ids=group_ids, fields=fields)

    @classmethod
    def group_short(cls, group_ids):
        return api.groups.getById(group_ids=group_ids)

    @classmethod
    def friends(cls, vkid):
        return api_app.friends.get(user_id=vkid)

    @classmethod
    def groups(cls, vkid):
        return api.groups.groups(user_id=vkid)

    @classmethod
    def search(cls, string, offset=0, limit=100, filters=''):
        logger.debub('Search %s', string)
        search_result = api.search.getHints(q=string, offset=offset,
                                            limit=limit, filters=filters, search_global=1)
        return search_result

    @classmethod
    def members(cls, group_id, amount=1000, offset=0, count=False):
        return api_app.groups.getMembers(group_id=group_id, offset=offset, count=amount)

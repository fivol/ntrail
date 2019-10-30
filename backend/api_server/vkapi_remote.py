import vk
from vk.exceptions import VkAPIError
import time
import math
from glbal import logger
import os
from constants import QUERY_RESULT_ACCESS_DENIED, \
    QUERY_RESULT_INVALID_ID, QUERY_RESULT_ERROR, \
    QUERY_RESULT_PRIVATE_PROFILE

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
        # logger.debug('* vk api request: %s', self.method1)
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
                logger.info('QUERY_RESULT_INVALID_ID')
                return QUERY_RESULT_INVALID_ID

            if e.code == 15:
                '''Access denied: this profile is private'''
                logger.info('QUERY_RESULT_ACCESS_DENIED')
                return QUERY_RESULT_ACCESS_DENIED

            if e.code == 30:
                '''vk.exceptions.VkAPIError: 30. This profile is private'''
                logger.info('QUERY_RESULT_PRIVATE_PROFILE')
                return QUERY_RESULT_PRIVATE_PROFILE

            self.method1, self.method2, self.kwargs = None, None, None
            raise e


user_token = '5211d7bcf46f21eb3e2e5bd64e75fa1199968260d81e170a8d21bb70758f14a46dd160009815ed8fcf94d'
api = API(session=vk.Session(access_token=user_token), v='5.102', lang='ru', timeout=10)

app_token = '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'
api_app = API(session=vk.Session(access_token=app_token), v='5.102', lang='ru', timeout=10)


class VKAPI:

    @classmethod
    def user(cls, users_ids, fields):
        users_ids = [int(vkid) for vkid in users_ids]
        result = api.users.get(user_ids=users_ids, fields=fields)

        if not isinstance(result, list):
            return [result] * len(users_ids)
        return result

    @classmethod
    def user_full(cls, users_ids):
        fields = [
            'photo_200', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
            'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
            'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
            'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
            'universities', 'verified', 'counters', 'screen_name', 'lists', 'is_closed',
        ]
        return cls.user(users_ids, fields=fields)

    @classmethod
    def user_short(cls, users_ids):
        return cls.user(users_ids, fields=[])

    @classmethod
    def resolve(cls, screen_name):
        assert isinstance(screen_name, str)
        return api_app.utils.resolveScreenName(screen_name=screen_name)

    @classmethod
    def group_full(cls, group_ids):
        fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                  'main_section', 'members_count', 'place',
                  'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                  'description', 'site', 'start_date']

        res = api.groups.getById(group_ids=group_ids, fields=fields)
        # print(res)
        return res

    @classmethod
    def group_short(cls, group_ids):
        return api.groups.getById(group_ids=group_ids)

    @classmethod
    def friends(cls, vkid):
        res = api_app.friends.get(user_id=vkid)
        assert isinstance(res, dict) or isinstance(res, str)
        return res

    @classmethod
    def groups(cls, vkid):
        return api.groups.get(user_id=vkid)

    @classmethod
    def search(cls, string, offset=0, limit=100, filters=''):
        search_result = api.search.getHints(q=string, offset=offset,
                                            limit=limit, filters=filters, search_global=1)
        return search_result

    @classmethod
    def members(cls, group_id, amount=1000, offset=0, count=False):
        return api_app.groups.getMembers(group_id=group_id, offset=offset, count=amount)

    @classmethod
    def execute(cls, code_string):
        assert isinstance(code_string, str)
        res = api.execute(code=code_string)
        return res

from tools import timeit
import vk
import time
import pickle
import math
from glbal import logger
import os
from tools import get

# vk app client_id 7091370
# service vk app key 7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1
# my user access_token 5bfaab47e81d46f1a1484571b5116939a4b142eb3253b715fa6af897018fd6662e7c41ada3ac04a63ed61
# vk error codes:
# 6 - too many requests per second;
# 30 - private user
# 15 - user deactivated

user_token_methods = ['groups']
service_token_methods = ['friends']


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
        except Exception as e:
            if e.code == 6:
                if time.time() - begin_time > 3:
                    logger.warning('Requests time limit exceeded! Sleep 3 seconds')
                    time.sleep(3)
                logger.warning(f'VK API error 6. Too many requests per second. Wait {wait_seconds} seconds')
                time.sleep(wait_seconds)
                return self.make_request(begin_time)

            self.method1, self.method2, self.kwargs = None, None, None
            raise e


user_token = '5211d7bcf46f21eb3e2e5bd64e75fa1199968260d81e170a8d21bb70758f14a46dd160009815ed8fcf94d'
api = API(session=vk.Session(access_token=user_token), v='5.69', lang='ru', timeout=10)

app_token = '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'
api_app = API(session=vk.Session(access_token=app_token), v='5.69', lang='ru', timeout=10)


class VKAPI:
    def __init__(self, verbose=1):
        self.verbose = verbose
        self.api_user = api
        self.api_app = api_app

    @classmethod
    def get_users(cls, vk_ids, full=False):

        have_users = [vkid for vkid in vk_ids if
                      vkid in get('users_data_') and get('users_data_')[vkid]['full'] >= full]
        to_save = [vkid for vkid in vk_ids if vkid not in have_users]

        if to_save:
            fields = []
            if full:
                fields = [
                    'photo_200', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
                    'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
                    'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
                    'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
                    'universities', 'verified', 'counters', 'screen_name'
                ]
            logger.debug('Get users data: %s', len(to_save))
            users = api.users.get(user_ids=to_save, fields=fields)
            for user in users:
                vkid = user['id']
                user['full'] = full
                get('users_data_')[vkid] = user

        return dict([(vkid, get('users_data_')[vkid]) for vkid in vk_ids if vkid in get('users_data_')])

    @classmethod
    def get_user(cls, vk_id, full=False):
        return cls.get_users([vk_id], full)[vk_id]

    @classmethod
    def get_random_group_users(cls, group_id, k=3000):
        request_groups = 1000
        res = cls.get_group_members(group_id=group_id, amount=request_groups, count=True)
        items = res['items']
        count = res['count']
        k -= request_groups
        count -= request_groups
        if k <= 0 or count <= 0:
            return items
        k_requests = math.ceil(k / request_groups)
        curr_offset = request_groups
        offset = math.ceil(count / k_requests)
        for i in range(k_requests):
            res = cls.get_group_members(group_id=group_id, offset=curr_offset, amount=request_groups)
            curr_offset += offset
            items += res

        return list(set(items))[:k]

    @classmethod
    def compare_groups(cls, group1, group2, k=3000):
        users1 = set(cls.get_random_group_users(group1, k=k))
        users2 = set(cls.get_random_group_users(group2, k=k))
        return len(users1.intersection(users2)) / k

    @classmethod
    def execute_query(cls, item_string, items_list, save_dict, default_value=None, msg=None):
        if not items_list:
            return []
        items_list = list(items_list)
        new_items_list = [item for item in items_list if item not in save_dict]

        if msg and new_items_list:
            logger.debug(f'{msg} {len(items_list)}')

        def execute_25(items):
            if not items:
                return []
            method = item_string.split('.')[1]
            if method in service_token_methods and len(items) == 1:
                code_str = item_string % items[0]
                code_str = 'api_app' + code_str[3:]
                code_str = code_str.replace('({', '(**{')
                try:
                    res = eval(code_str)
                except:
                    logger.exception('execute 25')
                    res = default_value
                return [res]
            code = 'return [' + \
                   ','.join(
                       [
                           item_string % item
                           for item in items
                       ],
                   ) + '];'
            res = api.execute(code=code)
            res = [i if i else [] for i in res]
            return res

        new_items = sum(
            [execute_25(new_items_list[a: a + 25])
             for a in range(0, len(new_items_list), 25)],
            []
        )
        for id, item in zip(new_items_list, new_items):
            save_dict[id] = item
        return [save_dict[id] for id in items_list]

    @classmethod
    def get_users_friends(cls, user_ids):
        return cls.execute_query('API.friends.get({"user_id":%d})["items"]', user_ids, get('users_friends_'),
                                 default_value=[], msg='Get users friends')

    @classmethod
    def get_users_groups(cls, user_ids):
        return cls.execute_query('API.groups.get({"user_id":%d})["items"]',
                                 user_ids, get('users_groups_'), default_value=[], msg='Get users groups')

    @classmethod
    def resolve_screen_names(cls, screen_names):
        return cls.execute_query('API.utils.resolveScreenName({"screen_name":"%s"})', screen_names,
                                 get('screen_names_'), msg='Resolve screen name')

    @classmethod
    def resolve_screen_name(cls, screen_name):
        return cls.resolve_screen_names([screen_name])[0]

    @classmethod
    def get_groups_data(cls, group_ids, one_by_one=False):
        # one_by_one fields: links counters
        fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                  'main_section', 'members_count', 'place',
                  'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                  'description', 'site', 'start_date']
        fields_string = ','.join(fields)
        if one_by_one and len(group_ids) > 1:
            return cls.execute_query(
                'API.groups.getById({"fields": "' + fields_string + '", "group_id":%d})[0]',
                group_ids,
                get('groups_data_'),
                msg='Get groups data'
            )
        new_items_ids = [item for item in group_ids if item not in get('groups_data_')]
        new_items = []
        if new_items_ids:
            logger.debug('Get short groups data: %s', len(new_items_ids))
            new_items = api.groups.getById(group_ids=new_items_ids, fields=fields)
        for id_, item in zip(new_items_ids, new_items):
            get('groups_data_')[id_] = item
        return [get('groups_data_')[id] for id in group_ids if id in get('groups_data_')]

    @classmethod
    def get_user_friends(cls, vkid):
        return cls.get_users_friends([vkid])[0]

    @classmethod
    def get_user_groups(cls, vkid):
        return cls.get_users_groups([vkid])[0]

    @classmethod
    def search(cls, string, offset=0, limit=100, filters='', users_ids=None):
        logger.debub('Search %s', string)
        search_result = api.search.getHints(q=string, offset=offset,
                                            limit=limit, filters=filters, search_global=1)
        if users_ids:
            return [item['profile']['id']
                    for item in search_result['items']
                    if item['type'] == 'profile']
        return search_result['items']

    @classmethod
    def get_group_members(cls, group_id, amount=1000, offset=0, count=False):
        if amount <= 1000:
            t = (group_id, offset, amount)
            if t in get('groups_members_'):
                res = get('groups_members_')[t]
            else:
                logger.debug('Get group members: %s amount: %s', group_id, amount)
                try:
                    res = api_app.groups.getMembers(group_id=group_id, offset=offset, count=amount)
                except Exception as e:
                    if e.code == 15:
                        res = {'items': [], 'count': 0}
                    else:
                        raise e
                get('groups_members_')[t] = res
            if count:
                return res
            return res['items']
        else:
            items = cls.get_group_members(group_id, offset, 1000)
            if len(items) < 1000:
                return items
            return items + cls.get_group_members(group_id, offset + 1000, amount - 1000)

    @classmethod
    def get_group_data(cls, group_id, full):
        return cls.get_groups_data([group_id], one_by_one=full)[0]

from baseapi import timeit
import vk
import time
import pickle
import math
import os
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
        print('* VK API Request: %s', self.method1)
        return self.make_request()

    def __getattr__(self, method_name):
        if not self.method1:
            self.method1 = method_name
        else:
            self.method2 = method_name
        return self

    def make_request(self, begin_time=None):
        # print('vk api request', self.method1)
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
            # print('ERROR')
            if e.code == 6:
                if time.time() - begin_time > 3:
                    print('Requests time limit exceeded! Sleep 3 seconds')
                    time.sleep(3)
                print(f'VK API error 6. Too many requests per second. Wait {wait_seconds} seconds')
                time.sleep(wait_seconds)
                return self.make_request(begin_time)

            self.method1, self.method2, self.kwargs = None, None, None
            raise e


user_token = '5211d7bcf46f21eb3e2e5bd64e75fa1199968260d81e170a8d21bb70758f14a46dd160009815ed8fcf94d'
api = API(session=vk.Session(access_token=user_token), v='5.69', lang='ru', timeout=10)

app_token = '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'
api_app = API(session=vk.Session(access_token=app_token), v='5.69', lang='ru', timeout=10)

users_data_ = {}
users_friends_ = {}
groups_data_ = {}
users_groups_ = {}
screen_names_ = {}
groups_members_ = {}

objects_to_save = [
    'users_data_',
    'users_friends_',
    'groups_data_',
    'users_groups_',
    'screen_names_',
    'groups_members_',
]


class VKAPI:
    def __init__(self, verbose=1):
        self.verbose = verbose
        self.api_user = api
        self.api_app = api_app

    @staticmethod
    def save_memory(file_name=None):
        try:
            with open('data/0last_memory_dump.info', 'r') as f:
                file_name = f.read()
        except FileNotFoundError:
            file_name = f'0{str(int(time.time()))}_memory_dump'
            with open('data/0last_memory_dump.info', 'w') as f:
                f.write(file_name)

        for name in objects_to_save:
            curr_file_name = f'{file_name}_{name}'
            with open('data/' + curr_file_name, 'wb') as f:
                pickle.dump(globals()[name], f)

        print('memory saved')

    @staticmethod
    def load_memory():
        try:
            with open('data/0last_memory_dump.info', 'r') as f:
                file_name = f.read()
                for name in objects_to_save:
                    curr_file_name = f'{file_name}_{name}'
                    with open('data/' + curr_file_name, 'rb') as f:
                        obj = pickle.load(f)
                        globals()[name] = obj

            print('memory loaded')
        except FileNotFoundError:
            print('Memory dump does not exits on path "data/"')

    def get_users(self, vk_ids, full=False):
        global users_data_
        
        have_users = [vkid for vkid in vk_ids if vkid in users_data_ and users_data_[vkid]['full'] >= full]
        to_save = [vkid for vkid in vk_ids if vkid not in have_users]
        
        if to_save:
            fields = []
            if full:
                fields = [
                    'photo_200', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
                    'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
                    'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
                    'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
                    'universities', 'verified', 'counters'
                ]
            users = api.users.get(user_ids=to_save, fields=fields)
            for user in users:
                vkid = user['id']
                if self.verbose >= 1:
                    print('* Get user data', vkid)
                user['full'] = full
                users_data_[vkid] = user
            
        return dict([(vkid, users_data_[vkid]) for vkid in vk_ids])
            
    def get_user(self, vk_id, full=False):
        return self.get_users([vk_id], full)[vk_id]

    def get_random_group_users(self, group_id, k=3000):
        request_groups = 1000
        res = self.get_group_members(group_id=group_id, amount=request_groups, count=True)
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
            res = self.get_group_members(group_id=group_id, offset=curr_offset, amount=request_groups)
            curr_offset += offset
            items += res

        return list(set(items))[:k]

    def compare_groups(self, group1, group2, k=3000):
        users1 = set(self.get_random_group_users(group1, k=k))
        users2 = set(self.get_random_group_users(group2, k=k))
        return len(users1.intersection(users2)) / k

    def execute_query(self, item_string, items_list, save_dict, default_value=None):
        items_list = list(items_list)
        new_items_list = [item for item in items_list if item not in save_dict]
        if not items_list:
            return []

        def execute_25(items):
            if not items:
                return []
            method = item_string.split('.')[1]
            if method in service_token_methods and len(items) == 1:
                code_str = item_string % items[0]
                code_str = 'api_app' + code_str[3:]
                code_str = code_str.replace('({', '(**{')
                # print(code_str)
                try:
                    res = eval(code_str)
                except Exception as e:
                    print(e)
                    # print('!! API Request ERROR. Default value', default_value)
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

    def get_users_friends(self, user_ids):
        # print('get_users_friends')
        return self.execute_query('API.friends.get({"user_id":%d})["items"]', user_ids, users_friends_, default_value=[])

    def get_users_groups(self, user_ids):
        return self.execute_query('API.groups.get({"user_id":%d})["items"]', user_ids, users_groups_, default_value=[])

    def resolve_screen_names(self, screen_names):
        return self.execute_query('API.utils.resolveScreenName({"screen_name":"%s"})', screen_names,
                                  screen_names_)

    def resolve_screen_name(self, screen_name):
        return self.resolve_screen_names([screen_name])[0]

    def get_groups_data(self, group_ids, one_by_one=False):
        if not group_ids:
            return []
        fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                  'main_section', 'members_count', 'place', 'public_date_label',
                  'trending', 'verified', 'wall', 'links']
        fields_string = ','.join(fields)
        if one_by_one and len(group_ids) > 1:
            return self.execute_query(
                'API.groups.getById({"fields": "' + fields_string + '", "group_id":%d})[0]',
                group_ids,
                groups_data_
            )
        new_items_ids = [item for item in group_ids if item not in groups_data_]
        # print(new_items_ids)
        new_items = []
        if new_items_ids:
            new_items = api.groups.getById(group_ids=new_items_ids, fields=fields)
        # print(new_items)
        for id, item in zip(new_items_ids, new_items):
            groups_data_[id] = item
        return [groups_data_[id] for id in group_ids if id in groups_data_]

    def get_user_friends(self, vkid):
        return self.get_users_friends([vkid])[0]

    def get_user_groups(self, vkid):
        return self.get_users_groups([vkid])[0]

    def search(self, string, offset=0, limit=100, filters='', users_ids=None):
        search_result = api.search.getHints(q=string, offset=offset,
                                            limit=limit, filters=filters, search_global=1)
        if users_ids:
            return [item['profile']['id']
                    for item in search_result['items']
                    if item['type'] == 'profile']
        return search_result['items']

    def get_group_members(self, group_id, offset=0, amount=1000, count=False):
        if amount <= 1000:
            t = (group_id, offset)
            if t in groups_members_:
                res = groups_members_[t]
            else:
                try:
                    res = api_app.groups.getMembers(group_id=group_id, offset=offset, count=amount)
                except Exception as e:
                    if e.code == 15:
                        res = {'items': [], 'count': 0}
                    else:
                        raise e
                groups_members_[t] = res
            if count:
                return res
            return res['items']
        else:
            items = self.get_group_members(group_id, offset, 1000)
            if len(items) < 1000:
                return items
            return items + self.get_group_members(group_id, offset + 1000, amount - 1000)

    def get_group_data(self, group_id):
        return self.get_groups_data([group_id])[0]


import math
from glbal import logger
from api_query import APIQueries

service = 'vk'


class VKAPI:
    @classmethod
    def get_users(cls, vk_ids, full=False, exe=True):
        if not vk_ids:
            return []
        assert isinstance(vk_ids, list)
        assert isinstance(vk_ids[0], int)
        method = 'user_' + ('full' if full else 'short')
        vk_ids = [str(item) for item in vk_ids]
        result = APIQueries().many(service, method, vk_ids, exe=exe)
        assert isinstance(result, list)
        assert len(result) == len(vk_ids)
        return result

    @classmethod
    def get_user(cls, vk_id, full=False, exe=True):
        assert isinstance(vk_id, int)
        return cls.get_users([vk_id], full=full, exe=exe)[0]

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
    def get_users_friends(cls, user_ids, exe=True):
        assert isinstance(user_ids, list)
        if not user_ids:
            return []
        assert isinstance(user_ids[0], int)
        user_ids = [str(vkid) for vkid in user_ids]
        res = APIQueries().many(service, 'friends', user_ids, exe=exe)
        assert len(res) == len(user_ids)
        result = []
        for friends in res:
            if isinstance(friends, dict):
                result.append(friends['items'])
            else:
                result.append([])

        return result

    @classmethod
    def get_user_friends(cls, vkid, exe=True):
        res = cls.get_users_friends([vkid], exe=exe)[0]
        if isinstance(res, str):
            return []
        assert isinstance(res, list), res
        return res

    @classmethod
    def get_users_groups(cls, user_ids, exe=True):
        user_ids = [str(vkid) for vkid in user_ids]
        res = APIQueries().many(service, 'groups', user_ids, exe=exe)
        assert isinstance(res, list)
        return [group['items'] for group in res if isinstance(group, dict)]

    @classmethod
    def get_user_groups(cls, vkid, exe=True):
        return cls.get_users_groups([vkid], exe=exe)[0]

    @classmethod
    def resolve_screen_names(cls, screen_names, exe=True):
        if not screen_names:
            return []
        res = APIQueries().many(service, 'resolve', screen_names, exe=exe)
        return res

    @classmethod
    def resolve_screen_name(cls, screen_name, exe=True):
        return cls.resolve_screen_names([screen_name], exe=exe)[0]

    @classmethod
    def get_groups_data(cls, group_ids, one_by_one=False, exe=True):
        if not group_ids:
            return []
        assert isinstance(group_ids[0], int)
        group_ids = [str(group) for group in group_ids]
        method = 'group_' + ('full' if one_by_one else 'short')
        return APIQueries().many(service, method, group_ids, exe=exe)

    @classmethod
    def get_group_data(cls, group_id, full):
        return cls.get_groups_data([group_id], one_by_one=full)[0]

    @classmethod
    def search(cls, string, offset=0, limit=100, filters='', users_ids=None, exe=True):
        logger.debub('Search %s', string)
        params = {
            'offset': offset,
            'limit': limit,
            'filters': filters,
            'users_ids': users_ids
        }
        return APIQueries().one(service, 'search', string, exe=exe, params=params)

    @classmethod
    def get_group_members(cls, group_id, amount=1000, offset=0, count=False, exe=True):
        params = {
            'amount': amount,
            'offset': offset,
            'count': count
        }
        return APIQueries().one(service, 'members', group_id, exe=exe, params=params)

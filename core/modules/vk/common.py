import logging
import math
from utils import list_from_dicts

logger = logging.getLogger('vk-api-module')


def get_items(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if isinstance(res, dict):
            return res.get('items', [])
        return []

    return wrapper


def log_query(func):
    def wrapper(*args, **kwargs):
        logger.info('Function: %s, %s %s', func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        logger.info('Result of %s is %s ', func.__name__, result)
        return result
    return wrapper


class VkCommon:
    @classmethod
    def get_users(cls, vk_ids, full=False, **kwargs):
        if not vk_ids:
            return []
        assert isinstance(vk_ids, list)
        assert isinstance(vk_ids[0], int)
        method = 'user_' + ('full' if full else 'short')
        vk_ids = [str(item) for item in vk_ids]
        result = APIQueries().many(service, method, vk_ids, **kwargs)
        assert isinstance(result, list)
        assert len(result) == len(vk_ids)
        return result

    @classmethod
    def get_user(cls, vk_id, full=False, **kwargs):
        assert isinstance(vk_id, int)
        user = cls.get_users([vk_id], full=full, **kwargs)[0]
        return user

    @classmethod
    def get_random_group_members(cls, group_id, k=3000):
        items_count = k
        # {} Можно оптимизировать запросы. Делать один вместо нескольких
        request_groups = 1000
        res = cls.get_group_members(group_id=group_id, count=request_groups, items=False)
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
            res = cls.get_group_members(group_id=group_id, offset=curr_offset, count=request_groups)
            assert isinstance(res, list)
            curr_offset += offset
            items += res
        return list(set(items))[:items_count]

    @classmethod
    def get_users_friends(cls, user_ids):
        assert isinstance(user_ids, list)
        if not user_ids:
            return []
        assert isinstance(user_ids[0], int)
        user_ids = [str(vkid) for vkid in user_ids]
        res = APIQueries().many(service, 'friends', user_ids)
        assert len(res) == len(user_ids)
        result = []
        for friends in res:
            if isinstance(friends, dict):
                result.append(friends['items'])
            else:
                result.append([])

        return result

    @classmethod
    @get_items
    def get_user_followers(cls, user_id):
        assert isinstance(user_id, int)
        return APIQueries().one(service, 'followers', str(user_id))

    @classmethod
    @get_items
    def get_user_subscriptions(cls, user_id):
        assert isinstance(user_id, int)
        res = APIQueries().one(service, 'subscriptions', str(user_id))
        if isinstance(res, dict):
            return res['users']
        return []

    @classmethod
    def get_user_friends(cls, vkid):
        res = cls.get_users_friends([vkid])[0]
        if isinstance(res, str):
            return []
        assert isinstance(res, list), res
        return res

    @classmethod
    def get_users_groups(cls, user_ids):
        user_ids = [str(vkid) for vkid in user_ids]
        res = APIQueries().many(service, 'groups', user_ids)
        assert isinstance(res, list)
        return [group['items'] for group in res if isinstance(group, dict)]

    @classmethod
    def get_user_groups(cls, vkid, count=None):
        params = {}
        if count:
            params['count'] = count

        res = APIQueries().one(service, 'groups', str(vkid), params=params)
        assert isinstance(res, dict)
        return res.get('items', [])

    @classmethod
    def resolve_screen_names(cls, screen_names):
        if not screen_names:
            return []
        res = APIQueries().many(service, 'resolve', screen_names)
        return res

    @classmethod
    def get_posts_by_ids(cls, post_ids):
        assert isinstance(post_ids, list)
        assert post_ids
        assert isinstance(post_ids[0], str)
        return APIQueries().many(service, 'posts', post_ids)

    @classmethod
    @get_items
    def get_comments(cls, post_id, count=100):
        assert isinstance(post_id, str)
        assert count <= 100
        comments = APIQueries().one(service, 'comments', post_id, params={'count': count})
        return comments

    @classmethod
    @get_items
    def get_photos_with_user(cls, user_id):
        return APIQueries().one(service, 'user_photos', str(user_id))

    @classmethod
    @get_items
    def get_albums(cls, obj_id):
        return APIQueries().one(service, 'albums', str(obj_id))

    @classmethod
    def get_albums_by_ids(cls, albums):
        assert isinstance(albums, list)
        if not albums:
            return []
        assert isinstance(albums[0], str)
        return APIQueries().many(service, 'albums_ids', albums)

    @classmethod
    @get_items
    def get_album_photos(cls, album_id):
        assert isinstance(album_id, str)
        res = APIQueries().one(service, 'photos', album_id)
        return res

    @classmethod
    def get_all_photos(cls, obj_id):
        res = APIQueries().one(service, 'all_photos', str(obj_id))
        if isinstance(res, dict):
            if res['count'] > len(res['items']):
                query = APIQueries()
                for offset in range(200, res['count'], 200):
                    query.add_query(BasicQuery(service, 'all_photos', str(obj_id), params={'offset': offset}))
                photos = res['items']
                results = query.execute()
                for res in results:
                    if isinstance(res, dict):
                        photos += res['items']
                return photos
            return res['items']
        return []

    @classmethod
    def get_photos_by_ids(cls, photos_ids):
        assert isinstance(photos_ids, list)
        if not photos_ids:
            return []
        assert isinstance(photos_ids[0], str)
        return APIQueries().many(service, 'photos_ids', photos_ids)

    @classmethod
    def get_photo_tags(cls, photo_id):
        assert isinstance(photo_id, str)
        return APIQueries().one(service, 'photo_tags', photo_id)

    @classmethod
    @get_items
    def get_posts(cls, obj, count):
        assert isinstance(obj, str)
        res = APIQueries().one(service, 'wall', obj, params={'count': count})
        return res

    @classmethod
    @get_items
    def get_object_likes(cls, obj_type, obj_id, count=1000):
        res = APIQueries().one(service, 'likes', f'{obj_type}_{obj_id}', params={'count': count})
        return res

    @classmethod
    def get_user_posts(cls, user_id, count=100):
        assert isinstance(user_id, int)
        return cls.get_posts(str(user_id), count)

    @classmethod
    def get_group_posts(cls, group_id, count=100):
        assert isinstance(group_id, int)
        return cls.get_posts('-' + str(group_id), count)

    @classmethod
    def resolve_screen_name(cls, screen_name):
        res = cls.resolve_screen_names([screen_name])[0]
        if not res:
            return {}
        return res

    @classmethod
    def get_groups_data(cls, group_ids, one_by_one=False, **kwargs):
        if not group_ids:
            return []
        assert isinstance(group_ids[0], int)
        group_ids = [str(group) for group in group_ids]
        method = 'group_' + ('full' if one_by_one else 'short')
        res = APIQueries().many(service, method, group_ids, **kwargs)
        assert isinstance(res, list)
        assert len(res) == len(group_ids)
        assert isinstance(res[0], dict), res
        return res

    @classmethod
    def get_group_data(cls, group_id, full, **kwargs):
        return cls.get_groups_data([group_id], one_by_one=full, **kwargs)[0]

    @classmethod
    def get_apps_data(cls, apps_id):
        assert isinstance(apps_id, list)
        if not apps_id:
            return []
        return APIQueries().many(service, 'apps', apps_id)

    @classmethod
    def search(cls, string, offset=0, limit=100, filters=''):
        logger.debug('Search %s', string)
        params = {
            'offset': offset,
            'limit': limit,
            'filters': filters,
        }
        return APIQueries().one(service, 'search', string, params=params)

    @classmethod
    def get_group_members(cls, group_id, count=1000, offset=0, items=True, force=False):
        assert isinstance(group_id, int)
        assert count > 0
        query_count = 1000
        queries_count = (count - 1) // query_count + 1
        logger.debug('Get groups members %s', group_id)
        assert isinstance(group_id, int)
        queries = APIQueries()
        group_id = str(group_id)
        while count > 0:
            params = {
                'offset': offset,
                'count': min(count, query_count)
            }
            queries.add_query(BasicQuery(service, 'members', group_id, params=params))
            count -= query_count
            offset += query_count

        results = queries.execute(force)
        assert len(results) == queries_count, len(results)
        if not isinstance(results[0], dict):
            return {
                'count': 0,
                'items': []
            }
        res = {
            'count': results[0]['count'],
            'items': sum(list_from_dicts(results, 'items'), [])
        }
        if items:
            return res['items']
        return res

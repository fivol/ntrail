import vk
from vk.exceptions import VkAPIError
import time
from glbal import logger
from ntapimodule.api_errors import VKError, INVALID_ID_ERROR, APIError


# module_vk app client_id 7091370
# service module_vk app key 7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1
# my user access_token 5bfaab47e81d46f1a1484571b5116939a4b142eb3253b715fa6af897018fd6662e7c41ada3ac04a63ed61


class API(vk.API):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method1 = None
        self.method2 = None
        self.kwargs = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        attempts_count = 3
        result = None
        for i in range(attempts_count):
            try:
                result = self.make_request()
                if isinstance(result, APIError) and not result.is_request_result():
                    continue
                break
            except:
                logger.exception('Fail to make VK request')
        self.method1, self.method2, self.kwargs = None, None, None
        if isinstance(result, APIError):
            return result.to_dict()
        assert not (result is None)
        return result

    def __getattr__(self, method_name):
        if not self.method1:
            self.method1 = method_name
        else:
            self.method2 = method_name
        return self

    def make_request(self, begin_time=None):
        if not begin_time:
            begin_time = time.time()
        try:
            res = super().__getattr__(self.method1)
            if self.method2:
                res = getattr(res, self.method2)
            res = res(**self.kwargs)
            return res
        except VkAPIError as e:
            if e.code == 6:
                wait_seconds = 1
                '''Too many requests'''
                if time.time() - begin_time > 3:
                    logger.warning('Requests time limit exceeded! Sleep 3 seconds')
                    time.sleep(3)
                else:
                    logger.warning(f'VK API error 6. Too many requests per second. Wait {wait_seconds} seconds')
                    time.sleep(wait_seconds)
                return self.make_request(begin_time)

            return VKError(e.code)


# user_token = '5211d7bcf46f21eb3e2e5bd64e75fa1199968260d81e170a8d21bb70758f14a46dd160009815ed8fcf94d'
# 19.09.20
user_token = 'e643452b7cc3fcbaf1c46540251eeffebbf1703154c498f919100c155f91fcd006300aa56f58dab88db16'
api = API(session=vk.Session(access_token=user_token), v='5.103', lang='ru', timeout=10)

app_token = '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'
# app_token = 'f375bcae59fa18e6fbe9f84d3f08947529ae4513c422dbdfead02901b4fc60ca05f05920311f7583e2d51'
api_app = API(session=vk.Session(access_token=app_token), v='5.103', lang='ru', timeout=10)

groups_full_fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                      'main_section', 'members_count', 'place',
                      'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                      'description', 'site', 'start_date']

users_full_fields = [
    'photo_200', 'photo_100', 'photo_max', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
    'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
    'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
    'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
    'universities', 'verified', 'counters', 'screen_name', 'lists', 'is_closed',
]


class VKAPI:

    @classmethod
    def user(cls, users_ids, fields):
        assert len(users_ids) <= 1000
        users_ids = [int(vkid) for vkid in users_ids]
        result = api.users.get(user_ids=users_ids, fields=fields)
        if VKError.is_error(result):
            return [result] * len(users_ids)
        assert isinstance(result, list), result
        if len(users_ids) != len(result):
            logger.warning('Fail to get several ids in user')
            for i, id in enumerate(users_ids):
                if i >= len(result):
                    result.append(VKError(INVALID_ID_ERROR).to_dict())
                else:
                    if result[i].get('id') != id:
                        result.insert(i, VKError(INVALID_ID_ERROR).to_dict())
        return result

    @classmethod
    def user_full(cls, users_ids):
        return cls.user(users_ids, fields=users_full_fields)

    @classmethod
    def user_short(cls, users_ids):
        return cls.user(users_ids, fields=[])

    @classmethod
    def resolve(cls, screen_name):
        assert isinstance(screen_name, str)
        return api_app.utils.resolveScreenName(screen_name=screen_name)

    @classmethod
    def group_full(cls, group_ids):
        assert len(group_ids) <= 500
        res = api.groups.getById(group_ids=group_ids, fields=groups_full_fields)
        return res

    @classmethod
    def group_short(cls, group_ids):
        assert len(group_ids) <= 500
        return api.groups.getById(group_ids=group_ids, fields=groups_full_fields)

    @classmethod
    def apps(cls, apps_id):
        res = api_app.apps.get(app_ids=apps_id)
        return res.get('items', None)

    @classmethod
    def friends(cls, vkid):
        res = api_app.friends.get(user_id=vkid)
        assert isinstance(res, dict) or isinstance(res, str)
        return res

    @classmethod
    def followers(cls, user_id, offset=0, count=1000):
        return api_app.users.getFollowers(user_id=user_id, offset=offset, count=count)

    @classmethod
    def subscriptions(cls, user_id, offset=0):
        return api_app.users.getSubscriptions(user_id=user_id, offset=offset, extended=0)

    @classmethod
    def wall(cls, obj_id, count):
        return api_app.wall.get(owner_id=obj_id, count=count, extended=0)

    @classmethod
    def posts(cls, post_ids):
        return api_app.wall.getById(posts=post_ids)

    @classmethod
    def likes(cls, object_id, count):
        obj_type, owner_id, item_id = object_id.split('_')
        return api_app.likes.getList(type=obj_type, owner_id=owner_id, item_id=item_id, count=count)

    @classmethod
    def comments(cls, post, count):
        owner_id, post_id = post.split('_')
        res = api_app.wall.getComments(owner_id=owner_id, post_id=post_id,
                                       need_likes=1, count=count, sort='asc',
                                       preview_length=0)
        return res

    @classmethod
    def albums(cls, obj_id, ids=None):
        if not ids:
            ids = []
        return api_app.photos.getAlbums(owner_id=obj_id, album_ids=ids)

    @classmethod
    def user_photos(cls, user_id):
        return api.photos.getUserPhotos(user_id=user_id, extended=True, count=1000)

    @classmethod
    def photo_tags(cls, photo_id):
        owner_id, photo_id = photo_id.split('_')
        return api.photos.getTags(owner_id=owner_id, photo_id=photo_id)

    @classmethod
    def albums_ids(cls, albums_ids):
        assert albums_ids
        assert isinstance(albums_ids, list)
        owner = albums_ids[0].split('_')[0]
        ids = [albums_ids[0].split('_')[1]]
        for album in albums_ids:
            assert owner == album.split('_')[0]
            ids.append(album.split('_')[1])
        albums = cls.albums(owner, ids=ids)

        if VKError.is_error(albums):
            logger.warning('Fail to get albums by ids')
            return [albums] * len(albums_ids)
        return albums.get('items', [])

    @classmethod
    def photos(cls, album):
        owner_id, album_id = album.split('_')
        return api_app.photos.get(owner_id=owner_id, album_id=album_id, extended=True)

    @classmethod
    def all_photos(cls, owner_id, offset=0):
        return api.photos.getAll(owner_id=owner_id, extended=True, count=200, offset=offset)

    @classmethod
    def photos_ids(cls, photos_ids):
        assert isinstance(photos_ids, list)
        res = api.photos.getById(photos=photos_ids, extended=True)
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
    def members(cls, group_id, count=None, offset=None):
        group_id = int(group_id)
        assert isinstance(count, int), count
        assert count <= 1000
        assert isinstance(offset, int)
        return api_app.groups.getMembers(group_id=group_id, offset=offset, count=count)

    @classmethod
    def execute(cls, code_string):
        assert isinstance(code_string, str)
        res = api.execute(code=code_string)
        return res

import typing

import celery as celery
import vk
import time
import asyncio
import typing
from random import randint

from aiovk import TokenSession, API
from aiovk.exceptions import VkCaptchaNeeded, VkTwoFactorCodeNeeded, VkAPIError
from collections import deque
from time import time

from session.session_manager import SessionManager
from ..parser import BaseParser
from ...config import logger

from .exceptions import VKError, INVALID_ID_ERROR

VK_API_VERSION = '5.103'
VK_API_LANG = 'ru'
# 10 секунд - ограничение на время выполнения запроса к API
VK_API_TIMEOUT = 10

# https://github.com/Fahreeve/aiovk


def create_vk_session(token: str):
    session = TokenSession(access_token=token)
    session.API_VERSION = '5.103'
    return API(session)


def session_error_handler(exc_type, exc_val, exc_tb):
    # TODO This is just example. Make normal
    if exc_type == VkAPIError:
        raise SessionWait(seconds=1)

    if exc_type == VkCaptchaNeeded:
        raise SessionRemove(reason='Captcha')


class ReliableAPI(vk.API):
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
            error = VKError(e.code)
            logger.warning('VKError %s', error)
            return error


class VkApiAccessor:
    """
    Предоставялетс интерфейс непосредственно для работы с API VK
    import vk
    Использует модуль "vk"
    Класс нужен для контроля за api сессиями и манипуляцией токенами
    для идентификации пользователя совершающего запрос
    """
    pass





# Токен приложения. Используется один на весь сервис
# Токен приложения нужен для выполнения некоторых запросов
# У него выше лимиты на простые, не требующее доступ к личной информации запросы
# TODO вынести в переменные окружения
app_token = '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'

# Список полей ответа API запроса, содержащего информацию о сообществах
groups_full_fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                      'main_section', 'members_count', 'place',
                      'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                      'description', 'site', 'start_date']

# Аналогично для людей. Список полей API запроса
users_full_fields = [
    'photo_200', 'photo_100', 'photo_max', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
    'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
    'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
    'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
    'universities', 'verified', 'counters', 'screen_name', 'lists', 'is_closed',
]


class CeleryTask(celery.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


class VkParser(BaseParser):
    """
    Производит запросы к ВК на основе
    готовых, чистых параметров запроса конкретного вида,
    переданных в аргументах.
    Класс содержит набор методов,
    каждый из которых соотносится одному или ряду
    (однородных) запросов
    Конструируется от токена пользователя, выполняющего запросы
    """

    @classmethod
    def resolve(cls, screen_name: str):
        return VkSessionManager.get_app_session().utils.resolveScreenName(screen_name=screen_name)

    @classmethod
    def friends(cls, user_id) -> typing.Union[dict, str]:
        return VkSessionManager.get_app_session().friends.get(user_id=user_id)

    # def user(self, users_ids, fields):
    #     assert len(users_ids) <= 1000
    #     users_ids = [int(vkid) for vkid in users_ids]
    #     result = self.api.users.get(user_ids=users_ids, fields=fields)
    #     if VKError.is_error(result):
    #         return [result] * len(users_ids)
    #     assert isinstance(result, list), result
    #     if len(users_ids) != len(result):
    #         logger.warning('Fail to get several ids in user')
    #         for i, id_ in enumerate(users_ids):
    #             if i >= len(result):
    #                 result.append(VKError(INVALID_ID_ERROR).to_dict())
    #             else:
    #                 if result[i].get('id') != id_:
    #                     result.insert(i, VKError(INVALID_ID_ERROR).to_dict())
    #     return result
    #
    # def user_full(self, users_ids):
    #     return self.user(users_ids, fields=users_full_fields)
    #
    # def user_short(self, users_ids):
    #     return self.user(users_ids, fields=[])
    #
    # def group_full(self, group_ids):
    #     assert len(group_ids) <= 500
    #     res = self.api.groups.getById(group_ids=group_ids, fields=groups_full_fields)
    #     return res
    #
    # def group_short(self, group_ids):
    #     assert len(group_ids) <= 500
    #     return self.api.groups.getById(group_ids=group_ids, fields=groups_full_fields)
    #
    # def apps(self, apps_id):
    #     res = api_app.apps.get(app_ids=apps_id)
    #     return res.get('items', None)
    #
    # def followers(self, user_id, offset=0, count=1000):
    #     return api_app.users.getFollowers(user_id=user_id, offset=offset, count=count)
    #
    # def subscriptions(self, user_id, offset=0):
    #     return api_app.users.getSubscriptions(user_id=user_id, offset=offset, extended=0)
    #
    # def wall(self, obj_id, count):
    #     return api_app.wall.get(owner_id=obj_id, count=count, extended=0)
    #
    # def posts(self, post_ids):
    #     return api_app.wall.getById(posts=post_ids)
    #
    # def likes(self, object_id, count):
    #     obj_type, owner_id, item_id = object_id.split('_')
    #     return api_app.likes.getList(type=obj_type, owner_id=owner_id, item_id=item_id, count=count)
    #
    # def comments(self, post, count):
    #     owner_id, post_id = post.split('_')
    #     res = api_app.wall.getComments(owner_id=owner_id, post_id=post_id,
    #                                    need_likes=1, count=count, sort='asc',
    #                                    preview_length=0)
    #     return res
    #
    # def albums(self, obj_id, ids=None):
    #     if not ids:
    #         ids = []
    #     return api_app.photos.getAlbums(owner_id=obj_id, album_ids=ids)
    #
    # def user_photos(self, user_id):
    #     return self.api.photos.getUserPhotos(user_id=user_id, extended=True, count=1000)
    #
    # def photo_tags(self, photo_id):
    #     owner_id, photo_id = photo_id.split('_')
    #     return self.api.photos.getTags(owner_id=owner_id, photo_id=photo_id)
    #
    # def albums_ids(self, albums_ids):
    #     assert albums_ids
    #     assert isinstance(albums_ids, list)
    #     owner = albums_ids[0].split('_')[0]
    #     ids = [albums_ids[0].split('_')[1]]
    #     for album in albums_ids:
    #         assert owner == album.split('_')[0]
    #         ids.append(album.split('_')[1])
    #     albums = self.albums(owner, ids=ids)
    #
    #     if VKError.is_error(albums):
    #         logger.warning('Fail to get albums by ids')
    #         return [albums] * len(albums_ids)
    #     return albums.get('items', [])
    #
    # def photos(self, album):
    #     owner_id, album_id = album.split('_')
    #     return api_app.photos.get(owner_id=owner_id, album_id=album_id, extended=True)
    #
    # def all_photos(self, owner_id, offset=0):
    #     return self.api.photos.getAll(owner_id=owner_id, extended=True, count=200, offset=offset)
    #
    # def photos_ids(self, photos_ids):
    #     assert isinstance(photos_ids, list)
    #     res = self.api.photos.getById(photos=photos_ids, extended=True)
    #     return res
    #
    # def groups(self, vkid):
    #     return self.api.groups.get(user_id=vkid)
    #
    # def search(self, string, offset=0, limit=100, filters=''):
    #     search_result = self.api.search.getHints(q=string, offset=offset,
    #                                              limit=limit, filters=filters, search_global=1)
    #     return search_result
    #
    # def members(self, group_id, count=None, offset=None):
    #     group_id = int(group_id)
    #     assert isinstance(count, int), count
    #     assert count <= 1000
    #     assert isinstance(offset, int)
    #     return api_app.groups.getMembers(group_id=group_id, offset=offset, count=count)
    #
    # def execute(self, code_string):
    #     assert isinstance(code_string, str)
    #     res = self.api.execute(code=code_string)
    #     return res


class VkMethods:
    user_api = SessionManager(key_type='vk.user.token',
                              session_maker=create_vk_session, error_handler=session_error_handler)
    app_api = SessionManager(key_type='vk.app.token',
                             session_maker=create_vk_session, error_handler=session_error_handler)

    # TODO Add ability to combine managers in context manager
    # To call any available api for example

    @classmethod
    async def _wrapper(cls, method, args, kwargs):
        try:
            method(*args, **kwargs)
        except SessionException:
            pass

    @classmethod
    async def user(cls, user_id):
        async with cls.user_api.get() as api:
            return await api.users.get(user_ids=user_id)
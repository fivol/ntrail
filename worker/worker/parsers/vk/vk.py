from worker.helpers.layers import method_logger
from worker.helpers.caching import redis_cache
from worker.parsers.layers import items_getter, mapped_method, reliable_call
from worker.parsers.parser import BaseParser
from worker.parsers.vk.data import *
from worker.parsers.vk.execute_pool import ExecuteRequestPool
from worker.parsers.vk.layers import *
from worker.parsers.vk.session import VkApiSession
from worker.session.exceptions import SessionManagerException, TokenAccessDenied, RpsLimitException
from worker.session.session_manager import SessionManager

from worker.helpers.tools import assert_imported_once, decorate
from worker.config import config
from worker.helpers.methods_injector import inject_methods_wrappers, ignore_injection

logger = logging.getLogger(__name__)

# 10 секунд - ограничение на время выполнения запроса к API
VK_API_TIMEOUT = 10

assert_imported_once()


@inject_methods_wrappers(method_logger(name=__name__), redis_cache, mapped_method)
class VKMethods(BaseParser):
    """
        Производит запросы к ВК на основе готовых, чистых параметров запроса конкретного вида, переданных в аргументах.
        Класс содержит набор методов, каждый из которых соотносится одному или ряду (однородных) запросов.
        Конструируется от токена пользователя, выполняющего запросы

        https://github.com/fivol/ntrail-worker/blob/167e705d0d55e8f97995d3c1831f326fbf213727/modules/vk/vk.py
    """
    # Vk requests limits https://vk.com/dev/api_requests
    # 3 in docs
    _user_api = SessionManager(key_type='vk.user', controller=VkApiSession, max_rps=config.vk.rps.user)
    # # 3 in docs
    _comm_api = SessionManager(key_type='vk.community', controller=VkApiSession, max_rps=config.vk.rps.community)
    # # 5 in docs
    _app_api = SessionManager(key_type='vk.app', controller=VkApiSession, max_rps=config.vk.rps.app)

    _execute_pool = ExecuteRequestPool()

    @classmethod
    @ignore_injection
    async def stop(cls):
        await cls._user_api.stop()
        await cls._comm_api.stop()
        await cls._app_api.stop()

    # TODO Add ability to combine managers in context manager
    # To call any available api for example

    @classmethod
    async def _call_api(cls, method, kwargs, apis, assert_response=False):
        for i, api in enumerate(apis):
            try:
                async with await api.get() as session:
                    result = await session(method, **kwargs, lang='ru')
                if not result and assert_response:
                    raise TokenAccessDenied()
                return result
            except SessionManagerException as e:
                if not isinstance(e, RpsLimitException):
                    logger.warning('Try next token: %s %s', type(e), e)
                if i == len(apis) - 1:
                    raise

    @classmethod
    async def _run_query(cls, method, kwargs, apis, executable=False, assert_response=False,
                         only_user_access=False, **other):
        """
        Runs vk query.
        Tried to group queries to execute it in single vk api execute commands
        If not enough commands, do is without execute, just with calling api
        """

        def handle_value(value):
            if isinstance(value, list):
                return ','.join(map(str, value))
            return value
        kwargs.update({key: value for key, value in other.items() if not key.startswith('_') and not key.endswith('_')})
        kwargs = {key: handle_value(value) for key, value in kwargs.items() if value}

        if not executable or True:
            response = await cls._call_api(method, kwargs, apis, assert_response=assert_response)
        else:
            response = await cls._execute_pool.try_use_execute(method, kwargs, only_user_access)
            if response is None:
                response = await cls._call_api(method, kwargs, apis, assert_response=assert_response)

        return response

    @classmethod
    @decorate(reliable_call, partition_split(1000))
    async def users(cls, user_ids: list, **kwargs) -> list:
        fields = users_full_fields
        return await cls._run_query(
            'users.get',
            {'user_ids': ','.join([str(id) for id in user_ids]), 'fields': fields},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True
        )

    @classmethod
    @decorate(reliable_call)
    async def execute(cls, code, only_user_access=False, **kwargs) -> list:
        return await cls._run_query(
            'execute',
            {'code': code}, ([] if only_user_access else [cls._comm_api]) + [cls._user_api],
            executable=False, **kwargs
        )

    @classmethod
    @decorate(reliable_call)
    async def resolve(cls, screen_name, **kwargs) -> dict:
        return await cls._run_query(
            'utils.resolveScreenName',
            {'screen_name': screen_name},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(5000))
    async def friends(cls, user_id, **kwargs) -> RichList:
        return await cls._run_query(
            'friends.get',
            {'user_id': user_id},
            [cls._app_api, cls._user_api],
            executable=True,
            **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000))
    async def followers(cls, user_id, **kwargs):
        return await cls._run_query(
            'users.getFollowers',
            {'user_id': user_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(200))
    async def subscriptions(cls, user_id, **kwargs):
        return await cls._run_query(
            'users.getFollowers',
            {'user_id': user_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, redis_cache, items_getter, count_offset_iterator(1000))
    async def members(cls, group_id, **kwargs) -> RichList:
        return await cls._run_query(
            'groups.getMembers',
            {'group_id': group_id},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True, only_user_access=True,
            **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000))
    async def groups(cls, user_id, **kwargs) -> RichList:
        return await cls._run_query(
            'groups.get',
            {'user_id': user_id},
            [cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, partition_split(500))
    async def groups_ids(cls, groups: list[str], **kwargs) -> list:
        return await cls._run_query(
            'groups.getById',
            {'group_ids': groups, 'fields': groups_full_fields},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000))
    async def photos(cls, owner_id, album_id: str, **kwargs) -> RichList:
        return await cls._run_query(
            'photos.get',
            {'owner_id': owner_id, 'album_id': album_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(200))
    async def photos_all(cls, owner_id, **kwargs) -> RichList:
        return await cls._run_query(
            'photos.getAll',
            {'owner_id': owner_id, 'extended': True},
            [cls._user_api],
            executable=True, only_user_access=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, partition_split(500))
    async def photos_ids(cls, photos: list[str], **kwargs) -> list:
        return await cls._run_query(
            'photos.getById',
            {'photos': photos},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, redis_cache, partition_split(100))
    async def posts_ids(cls, posts: list[str], **kwargs) -> list:
        return await cls._run_query(
            'wall.getById',
            {'posts': posts},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(100))
    async def posts(cls, owner_id=None, **kwargs) -> RichList:
        return await cls._run_query(
            'wall.get',
            {'owner_id': owner_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(100))
    async def likes(cls, owner_id=None, type_=None, item_id=None, **kwargs) -> RichList:
        # https://vk.com/dev/likes.getList
        return await cls._run_query(
            'likes.getList',
            {'owner_id': owner_id, 'type': type_, 'item_id': item_id},
            [cls._app_api, cls._user_api],
            executable=False, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(100))
    async def comments(cls, owner_id=None, post_id=None, **kwargs) -> RichList:
        # https://vk.com/dev/wall.getComments
        return await cls._run_query(
            'wall.getComments',
            {'owner_id': owner_id, 'post_id': post_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

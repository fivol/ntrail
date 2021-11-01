from aiovk import TokenSession, API
from aiovk.exceptions import VkAPIError

from worker.helpers.layers import method_logger
from worker.helpers.caching import redis_cache
from worker.parsers.parser import BaseParser
from worker.parsers.vk.data import *
from worker.parsers.vk.exceptions import VKError
from worker.parsers.vk.execute_pool import ExecuteRequestPool
from worker.parsers.vk.layers import *
from worker.session.exceptions import SessionManagerException
from worker.session.session_manager import SessionManager
from worker.session.session_state import SessionState
from worker.helpers.tools import assert_imported_once, decorate
from worker.ctx import get_context
from worker.config import config
from worker.helpers.methods_injector import inject_methods_wrappers, ignore_injection

logger = logging.getLogger('vk')

VK_API_VERSION = '5.103'
VK_API_LANG = 'ru'

# 10 секунд - ограничение на время выполнения запроса к API
VK_API_TIMEOUT = 10

assert_imported_once()

ctx = get_context()


class VkApiSession(SessionState):
    def __init__(self, *args, **kwargs):
        self.__vk_session = None
        super().__init__(*args, **kwargs)

    def create(self, key: str):
        session = TokenSession(access_token=key, timeout=ctx.timeout)
        self.__vk_session = session
        session.API_VERSION = VK_API_VERSION
        return API(session)

    async def close(self):
        await self.__vk_session.close()

    def handle_error(self, exc_type, exc_val, exc_tb):
        if exc_type == VkAPIError:
            error = VKError(error=exc_val)
            logger.warning('Catch vk api error: %s', error)
            raise error


@inject_methods_wrappers(method_logger(only_errors=True, name='injected'), make_synced)
class VkMethods(BaseParser):
    """
        Производит запросы к ВК на основе готовых, чистых параметров запроса конкретного вида, переданных в аргументах.
        Класс содержит набор методов, каждый из которых соотносится одному или ряду (однородных) запросов.
        Конструируется от токена пользователя, выполняющего запросы

        https://github.com/fivol/ntrail-worker/blob/167e705d0d55e8f97995d3c1831f326fbf213727/modules/vk/vk.py
    """
    # Vk requests limits https://vk.com/dev/api_requests
    # 3 in docs
    _user_api = SessionManager(key_type='vk.user.token', controller=VkApiSession, max_rps=config.vk.rps.user)
    # # 3 in docs
    _comm_api = SessionManager(key_type='vk.community.token', controller=VkApiSession, max_rps=config.vk.rps.community)
    # # 5 in docs
    _app_api = SessionManager(key_type='vk.app.token', controller=VkApiSession, max_rps=config.vk.rps.app)

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
    async def _call_api(cls, method, kwargs, apis):
        for i, api in enumerate(apis):
            try:
                with api.get() as session:
                    return await session(method, **kwargs)
            except SessionManagerException:
                if i == len(apis) - 1:
                    raise

    @classmethod
    async def _run_query(cls, method, kwargs, apis, executable=False, only_user_access=False, **other):
        """
        Runs vk query.
        Tried to group queries to execute it in single vk api execute commands
        If not enough commands, do is without execute, just with calling api
        """

        def handle_value(value):
            if isinstance(value, list):
                return ','.join(map(str, value))
            return value

        kwargs = {key: handle_value(value) for key, value in kwargs.items() if value}

        if not executable:
            return await cls._call_api(method, kwargs, apis)

        execute_result = await cls._execute_pool.try_use_execute(method, kwargs, only_user_access)
        if execute_result is None:
            return await cls._call_api(method, kwargs, apis)
        return execute_result

    @classmethod
    @decorate(reliable_call, method_logger(), partition_split(1000), redis_cache)
    async def users(cls, user_ids: list, full=False, **kwargs) -> dict:
        fields = []
        if full:
            fields = users_full_fields
        return await cls._run_query(
            'users.get',
            {'user_ids': ','.join([str(id) for id in user_ids]), 'fields': fields},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True
        )

    @classmethod
    @decorate(reliable_call, redis_cache)
    async def execute(cls, code, only_user_access=False, **kwargs) -> list:
        return await cls._run_query(
            'execute',
            {'code': code}, ([] if only_user_access else [cls._comm_api]) + [cls._user_api],
            executable=False, **kwargs
        )

    @classmethod
    @decorate(reliable_call, redis_cache)
    async def resolve(cls, screen_name, **kwargs) -> dict:
        return await cls._run_query(
            'utils.resolveScreenName',
            {'screen_name': screen_name},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(5000), redis_cache)
    async def friends(cls, user_id, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'friends.get',
            {'user_id': user_id},
            [cls._app_api, cls._user_api],
            executable=False,
            **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000), redis_cache)
    async def followers(cls, user_id, offset=0, count=1000, **kwargs):
        return await cls._run_query(
            'users.getFollowers',
            {'user_id': user_id, 'offset': offset, 'count': count},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, method_logger(name='low'), items_getter, count_offset_iterator(1000), redis_cache)
    async def members(cls, group_id, offset=0, count=1000, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'groups.getMembers',
            {'group_id': group_id, 'offset': offset, 'count': count},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True, only_user_access=True,
            **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000), redis_cache)
    async def groups(cls, user_id, offset=0, count=1000, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'groups.get',
            {'user_id': user_id, 'offset': offset, 'count': count},
            [cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, partition_split(500), redis_cache)
    async def photos(cls, owner_id=None, count=None, album_id='profile', **kwargs) -> ListWithCount:
        return await cls._run_query(
            'photos.get',
            {'owner_id': owner_id, 'count': count, 'album_id': album_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, partition_split(500), redis_cache)
    async def photos_ids(cls, photo_ids: list = None, **kwargs) -> list:
        return await cls._run_query(
            'photos.getById',
            {'photos': photo_ids},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

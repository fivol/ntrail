import asyncio
import json
import logging

from aiovk import TokenSession, API
from aiovk.exceptions import VkAPIError

from worker.helpers.caching import cache_with_redis
from worker.helpers.methods_injector import inject_methods_wrappers, ignore_injection
from worker.parsers.parser import BaseParser
from worker.parsers.vk.data import *
from worker.parsers.vk.exceptions import VKError
from worker.parsers.vk.layers import partition_split, count_offset_iterator, items_getter, ListWithCount, make_synced, \
    reliable_session_call
from worker.session.exceptions import SessionManagerException
from worker.session.session_manager import SessionManager
from worker.session.session_state import SessionState
from worker.helpers.tools import assert_imported_once, decorate

logger = logging.getLogger('vk')

VK_API_VERSION = '5.103'
VK_API_LANG = 'ru'

# 10 секунд - ограничение на время выполнения запроса к API
VK_API_TIMEOUT = 10

assert_imported_once()


class VkApiSession(SessionState):
    def __init__(self, *args, **kwargs):
        self.__vk_session = None
        super().__init__(*args, **kwargs)

    def create(self, key: str):
        session = TokenSession(access_token=key, timeout=3)
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


EXECUTE_QUERIES_BUNCH_COUNT = 25


class VkMethods(BaseParser):
    """
        Производит запросы к ВК на основе готовых, чистых параметров запроса конкретного вида, переданных в аргументах.
        Класс содержит набор методов, каждый из которых соотносится одному или ряду (однородных) запросов.
        Конструируется от токена пользователя, выполняющего запросы

        https://github.com/fivol/ntrail-worker/blob/167e705d0d55e8f97995d3c1831f326fbf213727/modules/vk/vk.py
    """
    # Vk requests limits https://vk.com/dev/api_requests
    # 3 in docs
    _user_api = SessionManager(key_type='vk.user.token', controller=VkApiSession, max_rps=3)
    # # 3 in docs
    _comm_api = SessionManager(key_type='vk.community.token', controller=VkApiSession, max_rps=3)
    # # 5 in docs
    _app_api = SessionManager(key_type='vk.app.token', controller=VkApiSession, max_rps=5)

    _execute_epoch = 0
    _execute_results = {}
    _executable_pool = []

    @classmethod
    @ignore_injection
    async def stop(cls):
        await cls._user_api.stop()
        await cls._comm_api.stop()
        await cls._app_api.stop()

    # TODO Add ability to combine managers in context manager
    # To call any available api for example



    @classmethod
    def _gen_execute_code(cls, items) -> str:
        """Item be like
        [('users.get', {'user_id': 123})]
        """
        commands = [
            f'API.{method_name}({json.dumps(kwargs, separators=(",", ":"))})'
            for method_name, kwargs in items
        ]
        return f'return [{",".join(commands)}];'

    @classmethod
    async def _run_execute_pool(cls, only_user_access=False):
        # Label results as waiting
        if not cls._executable_pool:
            raise IndexError
        logger.debug('Run execute pool %s', len(cls._executable_pool))
        execute_coro = cls.execute(cls._gen_execute_code(cls._executable_pool), only_user_access=only_user_access)
        execute_task = asyncio.create_task(execute_coro)

        cls._execute_results[cls._execute_epoch] = execute_task
        cls._execute_epoch += 1
        cls._executable_pool = []

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
        kwargs = {key: handle_value(value) for key, value in kwargs.items() if value is not None}

        async def run_with_api():
            for i, api in enumerate(apis):
                try:
                    with api.get() as session:
                        return await session(method, **kwargs)
                except SessionManagerException:
                    if i == len(apis) - 1:
                        raise

        if not executable:
            return await run_with_api()

        # Only for executable commands

        cmd_idx = len(cls._executable_pool)
        curr_epoch = cls._execute_epoch
        cls._executable_pool.append((method, kwargs))
        if len(cls._executable_pool) == EXECUTE_QUERIES_BUNCH_COUNT:
            await cls._run_execute_pool(only_user_access)

        # Very important. We should return control to collect many queries in pool in async
        await asyncio.sleep(0)
        if len(cls._executable_pool) < 15:
            await asyncio.sleep(0.001)
        if cls._execute_epoch == curr_epoch and len(cls._executable_pool) >= 3:
            await cls._run_execute_pool(only_user_access)
        results = cls._execute_results.get(curr_epoch, None)

        if results is None:
            cls._executable_pool = []
            return await run_with_api()

        if isinstance(results, asyncio.Task):
            real_results = await results
            cls._execute_results[curr_epoch] = [real_results, len(real_results)]

        results, remain_count = cls._execute_results[curr_epoch]
        assert isinstance(results, list)
        if results[0] is False:
            logger.warning('Execute query returns False')
            raise Warning('It seems, execute query failed')
        cls._execute_results[curr_epoch][1] -= 1
        result = results[cmd_idx]
        if not cls._execute_results[curr_epoch][1]:
            del cls._execute_results[curr_epoch]
        return result

    @classmethod
    @partition_split(1000)
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
    async def execute(cls, code, only_user_access=False, **kwargs) -> list:
        return await cls._run_query(
            'execute',
            {'code': code}, ([] if only_user_access else [cls._comm_api]) + [cls._user_api],
            executable=False,
        )

    @classmethod
    async def resolve(cls, screen_name, **kwargs) -> dict:
        return await cls._run_query(
            'utils.resolveScreenName',
            {'screen_name': screen_name},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True
        )

    @classmethod
    @items_getter
    async def friends(cls, user_id, **kwargs) -> list:
        return await cls._run_query(
            'friends.get',
            {'user_id': user_id},
            [cls._app_api, cls._user_api],
            executable=False,
            **kwargs
        )

    @classmethod
    @count_offset_iterator(1000)
    async def followers(cls, user_id, offset=0, count=1000, **kwargs):
        return await cls._run_query(
            'users.getFollowers',
            {'user_id': user_id, 'offset': offset, 'count': count},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @count_offset_iterator(1000)
    @items_getter
    async def members(cls, group_id, offset=0, count=1000, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'groups.getMembers',
            {'group_id': group_id, 'offset': offset, 'count': count},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True, only_user_access=True,
            **kwargs
        )

    @classmethod
    @count_offset_iterator(1000)
    @items_getter
    async def groups(cls, user_id, offset=0, count=1000, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'groups.get',
            {'user_id': user_id, 'offset': offset, 'count': count},
            [cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @items_getter
    async def photos(cls, owner_id=None, count=None, album_id='profile', **kwargs) -> ListWithCount:
        return await cls._run_query(
            'photos.get',
            {'owner_id': owner_id, 'count': count, 'album_id': album_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_session_call, partition_split(500), cache_with_redis, make_synced)
    async def photos_ids(cls, photo_ids: list = None, **kwargs) -> list:
        return await cls._run_query(
            'photos.getById',
            {'photos': photo_ids},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

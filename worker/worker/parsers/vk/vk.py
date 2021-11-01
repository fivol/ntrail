import asyncio
import json
import logging

from aiovk import TokenSession, API
from aiovk.exceptions import VkAPIError

from worker.helpers.caching import redis_cache
from worker.parsers.parser import BaseParser
from worker.parsers.vk.data import *
from worker.parsers.vk.exceptions import VKError
from worker.parsers.vk.layers import *
from worker.session.exceptions import SessionManagerException
from worker.session.session_manager import SessionManager
from worker.session.session_state import SessionState
from worker.helpers.tools import assert_imported_once, decorate
from worker.ctx import get_context

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


EXECUTE_QUERIES_BUNCH_COUNT = 25
EXECUTE_MAX_LENGTH = 12000


class ExecuteRequestPool:
    """
    https://vk.com/dev/execute
    """

    def __init__(self):
        self._execute_epoch = 0
        self._execute_results = {}
        self._executable_pool = []
        self._execute_length = 0

    @staticmethod
    def _gen_execute_code(items) -> str:
        """Item be like
        [('users.get', {'user_id': 123})]
        """
        commands = [
            f'API.{method_name}({json.dumps(kwargs, separators=(",", ":"))})'
            for method_name, kwargs in items
        ]
        return f'return [{",".join(commands)}];'

    async def _run_execute_pool(self, only_user_access=False):
        # Label results as waiting
        if not self._executable_pool:
            raise IndexError
        logger.debug('Run execute pool %s', len(self._executable_pool))
        code = self._gen_execute_code(self._executable_pool)
        execute_coro = VkMethods.execute(code, only_user_access=only_user_access)
        execute_task = asyncio.create_task(execute_coro)

        self._execute_results[self._execute_epoch] = execute_task
        self._execute_epoch += 1
        self._executable_pool = []
        self._execute_length = 0

    async def try_use_execute(self, method, kwargs, only_user_access=False):
        """Tries to add request to execute pool, if success returns result, else None"""
        cmd_idx = len(self._executable_pool)
        curr_epoch = self._execute_epoch
        cmd_length = len(json.dumps((method, kwargs)))

        if cmd_length > EXECUTE_MAX_LENGTH:
            logger.warning('Too long command to use execute command: %s', cmd_length)
            return None

        self._executable_pool.append((method, kwargs))
        self._execute_length += cmd_length
        if len(self._executable_pool) == EXECUTE_QUERIES_BUNCH_COUNT or \
                self._execute_length + cmd_length > EXECUTE_MAX_LENGTH:
            await self._run_execute_pool(only_user_access)

        # Very important. We should return control to collect many queries in pool in async
        await asyncio.sleep(0)
        if len(self._executable_pool) < 15:
            await asyncio.sleep(0.001)
        if self._execute_epoch == curr_epoch and len(self._executable_pool) >= 3:
            await self._run_execute_pool(only_user_access)
        results = self._execute_results.get(curr_epoch, None)

        if results is None:
            self._executable_pool = []
            return None

        if isinstance(results, asyncio.Task):
            real_results = await results
            self._execute_results[curr_epoch] = [real_results, len(real_results)]

        results, remain_count = self._execute_results[curr_epoch]
        assert isinstance(results, list)
        if results[0] is False:
            logger.warning('Execute query returns False')
            raise Warning('It seems, execute query failed')
        self._execute_results[curr_epoch][1] -= 1
        result = results[cmd_idx]
        if not self._execute_results[curr_epoch][1]:
            del self._execute_results[curr_epoch]
        return result


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

    _execute_pool = ExecuteRequestPool()

    @classmethod
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
    @decorate(reliable_call, partition_split(1000), redis_cache, make_synced)
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
    @decorate(reliable_call, redis_cache, make_synced)
    async def execute(cls, code, only_user_access=False, **kwargs) -> list:
        return await cls._run_query(
            'execute',
            {'code': code}, ([] if only_user_access else [cls._comm_api]) + [cls._user_api],
            executable=False, **kwargs
        )

    @classmethod
    @decorate(reliable_call, redis_cache, make_synced)
    async def resolve(cls, screen_name, **kwargs) -> dict:
        return await cls._run_query(
            'utils.resolveScreenName',
            {'screen_name': screen_name},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(5000), redis_cache, make_synced)
    async def friends(cls, user_id, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'friends.get',
            {'user_id': user_id},
            [cls._app_api, cls._user_api],
            executable=False,
            **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000), redis_cache, make_synced)
    async def followers(cls, user_id, offset=0, count=1000, **kwargs):
        return await cls._run_query(
            'users.getFollowers',
            {'user_id': user_id, 'offset': offset, 'count': count},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000), redis_cache, make_synced)
    async def members(cls, group_id, offset=0, count=1000, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'groups.getMembers',
            {'group_id': group_id, 'offset': offset, 'count': count},
            [cls._app_api, cls._comm_api, cls._user_api],
            executable=True, only_user_access=True,
            **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, count_offset_iterator(1000), redis_cache, make_synced)
    async def groups(cls, user_id, offset=0, count=1000, **kwargs) -> ListWithCount:
        return await cls._run_query(
            'groups.get',
            {'user_id': user_id, 'offset': offset, 'count': count},
            [cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, items_getter, partition_split(500), redis_cache, make_synced)
    async def photos(cls, owner_id=None, count=None, album_id='profile', **kwargs) -> ListWithCount:
        return await cls._run_query(
            'photos.get',
            {'owner_id': owner_id, 'count': count, 'album_id': album_id},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

    @classmethod
    @decorate(reliable_call, partition_split(500), redis_cache, make_synced)
    async def photos_ids(cls, photo_ids: list = None, **kwargs) -> list:
        return await cls._run_query(
            'photos.getById',
            {'photos': photo_ids},
            [cls._app_api, cls._user_api],
            executable=True, **kwargs
        )

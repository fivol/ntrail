import json
import time
import inspect
from collections import defaultdict

from celery_wrapper.app import app

import asyncio
import logging
import typing
from aiovk import TokenSession, API
from aiovk.exceptions import VkCaptchaNeeded, VkAPIError
from modules.parser import BaseParser

from session.exceptions import SessionWait, SessionRemove, NoTokenAvailableException, RpsLimitException, \
    SessionException, SessionManagerException
from session.session_manager import SessionManager
from session.session_state import SessionState
import config


logger = logging.getLogger('vk')

VK_API_VERSION = '5.103'
VK_API_LANG = 'ru'

# 10 секунд - ограничение на время выполнения запроса к API
VK_API_TIMEOUT = 10


class VkApiSession(SessionState):
    def __init__(self, *args, **kwargs):
        self.__vk_session = None
        super().__init__(*args, **kwargs)

    def create(self, key: str):
        session = TokenSession(access_token=key)
        self.__vk_session = session
        session.API_VERSION = VK_API_VERSION
        return API(session)

    async def close(self):
        await self.__vk_session.close()

    def handle_error(self, exc_type, exc_val, exc_tb):
        logger.info('Vk Api error handle')
        # TODO This is just example. Make normal
        # if exc_type == VkAPIError:
        #     raise SessionWait(seconds=1)
        #
        # if exc_type == VkCaptchaNeeded:
        #     raise SessionRemove(reason='Captcha')


def inject_methods_wrapper(wrapper_name):
    def cls_wrapper(cls):
        wrapper = getattr(cls, wrapper_name)
        for item in cls.__dict__:
            if item.startswith('_'):
                continue
            # TODO Skip all items, that is not methods
            method = getattr(cls, item)
            if not inspect.ismethod(method):
                continue

            class MethodWrapper:
                def __init__(self, _method, _wrapper):
                    self._method = _method
                    self._wrapper = _wrapper

                async def __call__(self, *args, **kwargs):
                    return await self._wrapper(self._method, args, kwargs)

            setattr(cls, item, MethodWrapper(method, wrapper))
        return cls

    return cls_wrapper


@inject_methods_wrapper('_wrapper')
class VkMethods:
    """
        Производит запросы к ВК на основе готовых, чистых параметров запроса конкретного вида, переданных в аргументах.
        Класс содержит набор методов, каждый из которых соотносится одному или ряду (однородных) запросов.
        Конструируется от токена пользователя, выполняющего запросы
    """
    # Vk requests limits https://vk.com/dev/api_requests
    # 3 in docs
    _user_api = SessionManager(key_type='vk.user.token', controller=VkApiSession, max_rps=3)
    # 5 in docs
    _app_api = SessionManager(key_type='vk.app.token', controller=VkApiSession, max_rps=5)

    _execute_epoch = 0
    _execute_results = {}
    _executable_pool = []

    # TODO Add ability to combine managers in context manager
    # To call any available api for example

    @classmethod
    async def _wrapper(cls, method, args, kwargs):
        while True:
            try:
                return await method(*args, **kwargs)
            except RpsLimitException:
                await asyncio.sleep(0.01)
                continue
            except NoTokenAvailableException:
                # TODO Think hard
                raise

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
    async def _run_execute_pool(cls):
        # Label results as waiting
        if not cls._executable_pool:
            raise IndexError
        logger.debug('Run execute pool %s', len(cls._executable_pool))
        execute_coro = cls.execute(cls._gen_execute_code(cls._executable_pool))
        execute_task = asyncio.create_task(execute_coro)

        cls._execute_results[cls._execute_epoch] = execute_task
        cls._execute_epoch += 1
        cls._executable_pool = []

    @classmethod
    async def _run_query(cls, method, kwargs, apis, executable=False) -> dict:
        """
        Runs vk query.
        Tried to group queries to execute it in single vk api execute commands
        If not enough commands, do is without execute, just with calling api
        """
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
        if len(cls._executable_pool) == 25:
            await cls._run_execute_pool()

        # Very important
        await asyncio.sleep(0)
        if cls._execute_epoch == curr_epoch and len(cls._executable_pool) >= 3:
            await cls._run_execute_pool()
        results = cls._execute_results.get(curr_epoch, None)

        if results is None:
            cls._executable_pool = []
            return await run_with_api()

        if isinstance(results, asyncio.Task):
            real_results = await results
            cls._execute_results[curr_epoch] = [real_results, len(real_results)]

        results, remain_count = cls._execute_results[curr_epoch]
        assert isinstance(results, list)
        cls._execute_results[curr_epoch][1] -= 1
        result = results[cmd_idx]
        if not cls._execute_results[curr_epoch][1]:
            del cls._execute_results[curr_epoch]
        return result

    @classmethod
    async def user(cls, user_id) -> dict:
        return await cls._run_query('users.get', {'user_id': user_id}, [cls._user_api, cls._app_api], executable=False)

    @classmethod
    async def friends(cls):
        return 0

    @classmethod
    async def execute(cls, code):
        with cls._user_api.get() as api:
            return await api.execute(code=code)
    #
    # @classmethod
    # async def resolve(cls, screen_name: str):
    #     async with cls.app_api.get() as api:
    #         return api.utils.resolveScreenName(screen_name=screen_name)
    #
    # @classmethod
    # async def friends(cls, user_id) -> typing.Union[dict, str]:
    #     async with cls.app_api.get() as api:
    #         return await api.friends.get(user_id=user_id)


async def main():
    t0 = time.time()
    count = 30
    ids = set([i for i in range(1, 1 + count)])
    users = await asyncio.gather(
        *[
            VkMethods.user(i)
            for i in ids
        ]
    )
    users_ids = {user[0]['id'] for user in users}
    assert ids == users_ids
    print(users)
    assert len(users) == count
    print(count / (time.time() - t0))

if __name__ == '__main__':
    asyncio.run(main())


import time

from celery_wrapper.app import app

import asyncio
import logging
import typing
from aiovk import TokenSession, API
from aiovk.exceptions import VkCaptchaNeeded, VkAPIError
import config
from modules.parser import BaseParser

from session.exceptions import SessionWait, SessionRemove, NoTokenAvailableException
from session.session_manager import SessionManager
from session.session_state import SessionState


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
        if exc_type == VkAPIError:
            raise SessionWait(seconds=1)

        if exc_type == VkCaptchaNeeded:
            raise SessionRemove(reason='Captcha')


class VkMethods:
    """
        Производит запросы к ВК на основе готовых, чистых параметров запроса конкретного вида, переданных в аргументах.
        Класс содержит набор методов, каждый из которых соотносится одному или ряду (однородных) запросов.
        Конструируется от токена пользователя, выполняющего запросы
    """
    user_api = SessionManager(key_type='vk.user.token', controller=VkApiSession)
    app_api = SessionManager(key_type='vk.app.token', controller=VkApiSession)

    # TODO Add ability to combine managers in context manager
    # To call any available api for example

    @classmethod
    async def user(cls, user_id) -> dict:
        while True:
            try:
                async with cls.app_api.get() as api:
                    return await api.users.get(user_ids=user_id)
            except NoTokenAvailableException:
                pass

    @classmethod
    async def resolve(cls, screen_name: str):
        async with cls.app_api.get() as api:
            return api.utils.resolveScreenName(screen_name=screen_name)

    @classmethod
    async def friends(cls, user_id) -> typing.Union[dict, str]:
        async with cls.app_api.get() as api:
            return await api.friends.get(user_id=user_id)


async def main():
    t0 = time.time()
    count = 500
    users = await asyncio.gather(
        *[
            VkMethods.user(_ + 10000)
            for _ in range(count)
        ]
    )
    print(len(users))
    print(users)
    assert len(users) == count
    print(count / (time.time() - t0))

if __name__ == '__main__':
    asyncio.run(main())


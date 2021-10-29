import asyncio
import typing
from aiovk import TokenSession, API
from aiovk.exceptions import VkCaptchaNeeded, VkAPIError

from session.exceptions import SessionWait, SessionRemove
from session.session_manager import SessionManager

VK_API_VERSION = '5.103'
VK_API_LANG = 'ru'

# 10 секунд - ограничение на время выполнения запроса к API
VK_API_TIMEOUT = 10


def create_vk_session(token: str):
    session = TokenSession(access_token=token)
    session.API_VERSION = VK_API_VERSION
    return API(session)


def session_error_handler(exc_type, exc_val, exc_tb):
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
    user_api = SessionManager(key_type='vk.user.token',
                              session_maker=create_vk_session, error_handler=session_error_handler)
    app_api = SessionManager(key_type='vk.app.token',
                             session_maker=create_vk_session, error_handler=session_error_handler)

    # TODO Add ability to combine managers in context manager
    # To call any available api for example

    @classmethod
    async def user(cls, user_id) -> dict:
        async with cls.user_api.get() as api:
            print(api, type(api))
            return await api.users.get(user_ids=user_id)

    @classmethod
    async def resolve(cls, screen_name: str):
        async with cls.app_api.get() as api:
            return api.utils.resolveScreenName(screen_name=screen_name)

    @classmethod
    async def friends(cls, user_id) -> typing.Union[dict, str]:
        async with cls.app_api.get() as api:
            return api.friends.get(user_id=user_id)


async def main():
    print(await VkMethods.user(1))

if __name__ == '__main__':
    asyncio.run(main())


import logging

from aiovk import TokenSession, API
from aiovk.exceptions import VkAPIError, VkAuthError

from worker.config import config
from worker.credentials.access import AccessModel
from worker.ctx import get_context
from worker.parsers.vk.exceptions import VKError, VKErrorType
from worker.session.exceptions import SessionRemove, TokenAccessDenied
from worker.session.session_state import SessionState


VK_API_VERSION = '5.103'
VK_API_LANG = 'ru'

ctx = get_context()

logger = logging.getLogger(__name__)


class VkApiSession(SessionState):
    def __init__(self, *args, **kwargs):
        self.__vk_session = None
        super().__init__(*args, **kwargs)

    def create(self, access: AccessModel):
        key = access.token
        session = TokenSession(access_token=key, timeout=config.get('vk.timeout', 1))
        self.__vk_session = session
        session.API_VERSION = VK_API_VERSION
        return API(session)

    async def close(self):
        await self.__vk_session.close()

    def handle_error(self, exc_type, exc_val, exc_tb):
        if exc_type == VkAPIError:
            error = VKError(error=exc_val)
            logger.warning('Catch vk api error: %s', error)
            if error.type == VKErrorType.ACCESS_DENIED:
                raise TokenAccessDenied()
            if error.type == VKErrorType.GROUP_AUTHORIZATION_FAILED:
                raise SessionRemove()
            raise error
        if exc_type == VkAuthError:
            raise SessionRemove()

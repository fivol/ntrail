from core import VKUser
from server.plugin.plugin import InputPlugin, BasePlugin


class VKUserInput(InputPlugin):
    name = 'user'

    @classmethod
    async def read(cls, user: str, **kwargs) -> dict:
        return {
            'user': await VKUser.create(user)
        }


class VKFriendsInput(InputPlugin):
    name = 'friends'

    @classmethod
    def read(cls, user: VKUser, **kwargs) -> dict:
        return {
            'community': user.friends()
        }


class VKGroupsInput(InputPlugin):
    name = 'user-groups'

    @classmethod
    def read(cls, user: VKUser, **kwargs) -> dict:
        return {
            'groups': user.groups()
        }


class VKUserData(BasePlugin):
    name = 'user'

    def __init__(self, user: VKUser, **kwargs):
        super().__init__(**kwargs)
        self._user = user

    async def response(self) -> dict:
        return await self._user.summary()

    def data(self):
        return self._user.data()

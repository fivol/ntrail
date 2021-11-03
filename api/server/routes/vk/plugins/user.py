from core import VKUser
from server.plugin.plugin import InputPlugin, BasePlugin


class VKUserInput(InputPlugin):
    name = 'user'

    @classmethod
    def read(cls, user: str, **kwargs) -> dict:
        return {
            'user': VKUser(user)
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

    def response(self) -> dict:
        return self._user.data()

    def summery(self):
        return self._user.summary()

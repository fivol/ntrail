from core import VKUser
from server.plugin.plugin import InputPlugin


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

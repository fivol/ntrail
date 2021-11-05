from core import VKUser
from core.constants import AccountStatus, NO_AVA_IMG
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
    async def read(cls, user: VKUser, **kwargs) -> dict:
        return {
            'community': await user.friends()
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
        user = self._user
        result = {
            'valid': await user.valid(),
            'status': (await user.status()).name,
            'img': 'https://vk.com/images/deactivated_100.png?ava=1',
            'name': 'Пользователь не валиден',
        }
        if not await self._user.valid():
            return result
        data = await self.data()
        return {
            **result,
            'id': user.id,
            'url': user.url,
            'name': await user.name(),
            'img': data.get('photo_200', NO_AVA_IMG),
            'username': data.get("screen_name", 'id' + str(user.id)),
            'verified': data.get('verified', False),
            'private': await user.status() == AccountStatus.PRIVATE,
        }

    def data(self):
        return self._user.data()

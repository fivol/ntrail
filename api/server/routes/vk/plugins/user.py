import re
import typing
from datetime import datetime

from core import VKUser
from core.constants import AccountStatus, NO_AVA_IMG
from server.plugin.plugin import InputPlugin, BasePlugin
from server.routes.vk.features.register_date import UserRegistrationDate
from server.routes.vk.plugins.friends import UserFriendsPlugin


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

    def registration(self):
        return UserRegistrationDate.date(self._user.id).isoformat()

    def is_fake(self):
        # TODO AAAAAAA
        return (datetime.now() - UserRegistrationDate.date(self._user.id)).days < 365 * 2

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


class UserDescribePlugin(BasePlugin):
    name = 'user-describe'

    def __init__(self, user: VKUser, **kwargs):
        super(UserDescribePlugin, self).__init__(**kwargs)
        self._user = user
        self._friends = UserFriendsPlugin(self._user)

    async def init(self):
        await self._friends.init()

    async def age(self):
        data = await self._user.data()
        age = data.get('bdate')
        day = None
        month = None
        year = None
        age_years = None
        if age:
            try:
                full_age = datetime.strptime(age, '%d.%m.%Y')
                day = full_age.day
                month = full_age.month
                year = full_age.year
                age_years = (datetime.now() - full_age).days / 365
            except ValueError:
                pass
            if not day:
                age = datetime.strptime(age, '%d.%m')
                day = age.day
                month = age.month
        if not age_years:
            age_years = self._friends.age()

        return {
            'year': year,
            'month': month,
            'day': day,
            'age': age_years
        }

    @classmethod
    def _try_parse_instagram_str(cls, text, reg):
        match = re.search(reg, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    async def instagram(self):
        data = await self._user.data()
        username = data.get('instagram', '')
        site = data.get('site', '')
        status = data.get('status', '')

        username_reg = r'([a-z_.-]+)'
        inst_reg = [
            fr'instagram.com/{username_reg}',
            fr'inst:\s*{username_reg}',
            fr'inst\s+{username_reg}',
            fr'inst\s*-\s*{username_reg}',
        ]
        texts = [site, status]
        for text in texts:
            if username:
                break
            for reg in inst_reg:
                if username:
                    username = self._try_parse_instagram_str(text, reg)

        if username:
            return f'https://instagram.com/{username}'
        return None

    async def response(self) -> typing.Union[dict, list]:

        return {
            'age': await self.age(),
            'instagram': await self.instagram()
        }

import re
import typing
from datetime import datetime

from loguru import logger

from core import VKUser
from core.constants import AccountStatus, NO_AVA_IMG
from server.plugin.plugin import InputPlugin, BasePlugin
from server.routes.vk.features.register_date import UserRegistrationDate
from server.routes.vk.plugins.friends import VKUserFriendsPlugin


class VKUserInput(InputPlugin):
    name = 'user'
    namespace = 'vk'

    @classmethod
    async def read(cls, user: str, **kwargs) -> dict:
        return {
            'user': await VKUser.create(user)
        }


class VKFriendsInput(InputPlugin):
    name = 'friends'
    namespace = 'vk'

    @classmethod
    async def read(cls, user: VKUser, **kwargs) -> dict:
        return {
            'community': await user.friends()
        }


class VKGroupsInput(InputPlugin):
    name = 'user-groups'
    namespace = 'vk'

    @classmethod
    def read(cls, user: VKUser, **kwargs) -> dict:
        return {
            'groups': user.groups()
        }


class VKUserPlugin(BasePlugin):
    name = 'user'
    namespace = 'vk'

    def __init__(self, user: VKUser, **kwargs):
        logger.debug('User plugin: user-{}', user)
        super().__init__(**kwargs)
        self._user = user
        self._data = None

    async def init(self):
        self._data = await self._user.data()

    def registration(self):
        return UserRegistrationDate.date(self._user.id).isoformat()

    @classmethod
    def _try_parse_instagram_str(cls, text, reg):
        match = re.search(reg, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def instagram(self):
        data = self._data
        username = data.get('instagram', '').strip()
        site = data.get('site', '')
        status = data.get('status', '')

        username_reg = r'([a-z_.-]+)'
        inst_reg = [
            fr'instagram.com/{username_reg}',
            fr'inst:\s*{username_reg}',
            fr'inst:\s*@\s*{username_reg}',
            fr'inst\s+{username_reg}',
            fr'inst\s*-\s*{username_reg}',
        ]
        texts = [site, status]
        for text in texts:
            if username:
                break
            for reg in inst_reg:
                username = self._try_parse_instagram_str(text, reg)
                if username:
                    break

        if username:
            return f'https://instagram.com/{username}'
        return None

    def age(self):
        data = self._data
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

        return {
            'year': year,
            'month': month,
            'day': day,
            'age': age_years
        }

    def city(self):
        return self._data.get('city', {}).get('title') or self._data.get('home_town')

    async def data(self):
        return await self._user.data()

    async def groups(self):
        groups = await self._user.groups()
        return await groups.data()

    async def response(self) -> dict:
        user = self._user
        result = {
            'valid': await user.valid(),
            'status': (await user.status()).name,
            'img': 'https://vk.com/images/deactivated_100.png?ava=1',
            'name': 'Пользователь не валиден',
        }
        logger.info('User plugin result: {}', result)
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
            'instagram': self.instagram(),
        }


class UserDescribePlugin(BasePlugin):
    name = 'user-describe'
    namespace = 'vk'

    def __init__(self, user: VKUser, **kwargs):
        super(UserDescribePlugin, self).__init__(**kwargs)
        self._user = user
        self._user_plugin = VKUserPlugin(user=user)
        self._friends_plugin = VKUserFriendsPlugin(self._user)

    async def init(self):
        await self._user_plugin.init()
        await self._friends_plugin.init()

    def is_fake(self):
        # TODO AAAAAAA
        return (datetime.now() - UserRegistrationDate.date(self._user.id)).days < 365 * 2

    def age(self):
        age = self._user_plugin.age()
        if not age.get('age'):
            age['age'] = self._friends_plugin.age()
        return age

    def city(self):
        return self._user_plugin.city() or self._friends_plugin.city()

    async def response(self) -> typing.Union[dict, list]:
        return {
            'age': self.age(),
            'city': self.city(),
            'is_fake': self.is_fake()
        }

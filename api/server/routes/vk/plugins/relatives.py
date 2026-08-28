from contextlib import suppress

from core import VKUser
from server.plugin.plugin import BasePlugin
from core import VKCommunity
from server.routes.vk.plugins.user import UserDescribePlugin
from worker import VKError

MAX_SIBLING_AGE_DIFF = 7


class VKRelativesPlugin(BasePlugin):
    name = 'relatives'
    namespace = 'vk'

    def __init__(self, user: VKUser, **kwargs):
        super().__init__(**kwargs)
        self._user = user
        self._relatives = []
        self._ids = set()
        self._ids.add(self._user.id)
        self._age = {}

    async def init(self):
        user = UserDescribePlugin(self._user)
        await user.init()
        self._age = user.age() or {}

    @classmethod
    def _is_same_surname(cls, s1: str, s2: str):
        if not s1 or not s2:
            return False
        if s1.startswith(s2) or s2.startswith(s1):
            return True
        return False

    async def _add_relative(self, name, url, type_, sex, user=None):
        id_ = url or name
        if id_ in self._ids:
            return

        self._ids.add(id_)

        if not type_ and user:
            with suppress(VKError):
                user_desc = UserDescribePlugin(user)
                await user_desc.init()
                age = user_desc.age()
                if age.get('age') and self._age.get('age'):
                    if abs(age['age'] - self._age['age']) <= MAX_SIBLING_AGE_DIFF:
                        type_ = 'sibling'
                    elif age['age'] - self._age['age'] > MAX_SIBLING_AGE_DIFF:
                        type_ = 'parent'
                    elif self._age['age'] - age['age'] > MAX_SIBLING_AGE_DIFF:
                        type_ = 'child'

        self._relatives.append({
            'name': name,
            'url': url,
            'type': type_,
            'sex': sex
        })

    @classmethod
    def _reverse_relative_type(cls, type_: str):
        return {
            'child': 'parent',
            'sibling': 'sibling',
            'parent': 'child',
            'grandparent': 'grandchild',
            'grandchild': 'grandparent',
        }.get(type_)

    async def response(self) -> list[dict]:
        relatives = []

        data = await self._user.data()
        relatives += data.get('relatives', [])

        friends = await self._user.friends()
        await friends.preload()
        same_surnames = [user for user in friends.objects() if
                         self._is_same_surname(user.last_name, self._user.last_name)]
        relatives += same_surnames
        relative_names = [user.full_name for user in same_surnames]
        relative_names.append(self._user.full_name)

        for user in same_surnames:
            relatives += (await user.data()).get('relatives', [])

        for user in friends.objects():
            user_relatives = (await user.data()).get('relatives', [])
            for item in user_relatives:
                if item.get('id') == self._user.id or item.get('name') and item.get('name') in relative_names:
                    item['type'] = self._reverse_relative_type(item['type'])
                    relatives.append(item)

        users = []
        for item in relatives:
            if isinstance(item, dict) and not item.get('id'):
                await self._add_relative(item['name'], None, item['type'], None)
            else:
                users.append(item)

        community = VKCommunity([user.id if isinstance(user, VKUser) else user['id'] for user in users])
        await community.preload()
        for user, item in zip(community, users):
            if isinstance(item, VKUser):
                await self._add_relative(user.first_name, user.url, None, user.sex, user=user)
            else:
                await self._add_relative(user.first_name, user.url, item['type'], user.sex, user=user)

        return self._relatives

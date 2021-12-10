import typing
from pprint import pprint

from server.plugin.plugin import BasePlugin
from server.routes.vk.plugins.community import VKCommunityPlugin


class UserFriendsPlugin(BasePlugin):
    name = 'user-friends'

    def __init__(self, user, **kwargs):
        super(UserFriendsPlugin, self).__init__(**kwargs)
        self._user = user
        self._friends: typing.Optional[VKCommunityPlugin] = None
        self._processed = None

    async def init(self):
        self._friends = VKCommunityPlugin(await self._user.friends())
        self._processed = await self._friends.processed()

    def school(self) -> typing.Optional[str]:
        prop = self._processed['school']
        if self._friends.prop_importance(prop) > 0.4:
            return prop.first().value
        return None

    def university(self) -> typing.Optional[str]:
        # TODO refactor this hell
        prop = self._processed['university']
        if self._friends.prop_importance(prop) > 0.4:
            return prop.first().value
        return None

    def age(self):
        age = self._processed['age']
        return age.get('commonMean')

    def city(self):
        pprint(self._processed)
        city = self._processed.get('city', {}).get('source_list')
        if city:
            return city[0][0].value

    async def response(self) -> dict:
        return {
            'school': self.school(),
            'university': self.university(),
            'age': self.age(),
        }

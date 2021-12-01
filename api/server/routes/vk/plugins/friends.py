import typing

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

    async def response(self) -> dict:
        return {
            'school': self.school(),
            'university': self.university(),
            'age': self.age(),
        }

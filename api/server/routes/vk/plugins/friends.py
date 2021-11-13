import typing

from server.plugin.plugin import BasePlugin
from server.routes.vk.plugins.community import VKCommunityPlugin


class UserFriendsPlugin(BasePlugin):
    name = 'user-friends'

    def __init__(self, user, **kwargs):
        super(UserFriendsPlugin, self).__init__(**kwargs)
        self._user = user
        self._friends: typing.Optional[VKCommunityPlugin] = None

    async def init(self):
        self._friends = VKCommunityPlugin(await self._user.friends())

    async def school(self) -> typing.Optional[str]:
        processed = await self._friends.processed()
        prop = processed['school']
        if self._friends.prop_importance(prop) > 0.4:
            return prop.first().value
        return None

    async def university(self) -> typing.Optional[str]:
        # TODO refactor this hell
        processed = await self._friends.processed()
        prop = processed['university']
        if self._friends.prop_importance(prop) > 0.4:
            return prop.first().value
        return None

    async def response(self) -> dict:
        return {
            'school': await self.school(),
            'university': await self.university(),
        }

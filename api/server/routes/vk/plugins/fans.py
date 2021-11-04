import asyncio

from core import VKUser, VKCommunity
from server.plugin.plugin import BasePlugin
from collections import Counter


class UserFansPlugin(BasePlugin):
    name = 'user-fans'

    def __init__(self, user: VKUser, **kwargs):
        super(UserFansPlugin, self).__init__(**kwargs)
        self._user = user

    async def response(self) -> list:
        posts = await self._user.posts()
        likes = await asyncio.gather(*[post.likes() for post in posts])
        likes = sum(likes, start=VKCommunity())
        users = likes.counter().most_common()[:3]
        names = await asyncio.gather(*[VKUser(user[0]).name() for user in users])
        return [
            {
                'id': user_id,
                'url': VKUser(user_id).url,
                'name': name,
                'weight': count
            }
            for (user_id, count), name in zip(users, names)
        ]

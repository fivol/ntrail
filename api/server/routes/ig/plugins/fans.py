import asyncio
from collections import Counter

from core import IGUser, IGCommunity
from server.plugin.plugin import BasePlugin


class IGUserFans(BasePlugin):
    name = 'user-fans'
    namespace = 'ig'

    def __init__(self, user: IGUser, **kwargs):
        super(IGUserFans, self).__init__(**kwargs)
        self._user: IGUser = user

    async def response(self):
        if not await self._user.valid():
            return None
        posts = await self._user.wall()
        likes = await asyncio.gather(*[post.likes() for post in posts], return_exceptions=True)
        likes = list(filter(lambda x: not isinstance(x, Exception), likes))
        likes = sum(likes, start=IGCommunity())

        top_likes = likes.select(count=10, break_point=1)

        counter = top_likes.counter()
        users = await top_likes.data()
        users = [{**user, 'weight': counter[user['id']]} for user in users]
        return [
            {
                'id': user['id'],
                'url': IGUser(user).url,
                'name': IGUser(user).full_name,
                'weight': user['weight']
            }
            for user in users[:5]
        ]

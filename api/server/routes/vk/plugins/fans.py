import asyncio

from core import VKUser, VKCommunity
from server.plugin.plugin import BasePlugin


class UserFansPlugin(BasePlugin):
    name = 'user-fans'

    def __init__(self, user: VKUser, **kwargs):
        super(UserFansPlugin, self).__init__(**kwargs)
        self._user = user

    async def response(self) -> list:
        my_sex = (await self._user.data()).get('sex')
        posts = await self._user.posts(all_=False)
        likes = await asyncio.gather(*[post.likes() for post in posts.objects()])
        likes = sum(likes, start=VKCommunity())
        top_likes = likes.select(count=10, break_point=1)
        top_likes = await top_likes.only_valid()
        counter = top_likes.counter()
        users = await top_likes.data()
        users = [{**user, 'weight': counter[user['id']]} for user in users]
        other_sex = filter(lambda user: user['sex'] != my_sex, users)
        return [
            {
                'id': user['id'],
                'url': VKUser(user['id']).url,
                'name': await VKUser(user).name(),
                'weight': user['weight']
            }
            for user in other_sex
        ]

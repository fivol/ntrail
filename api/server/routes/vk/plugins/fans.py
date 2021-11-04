from core import VKUser, VKCommunity
from server.plugin.plugin import BasePlugin
from collections import Counter


class UserFansPlugin(BasePlugin):
    name = 'user-fans'

    def __init__(self, user: VKUser, **kwargs):
        super(UserFansPlugin, self).__init__(**kwargs)
        self._user = user

    def response(self) -> list:
        posts = self._user.posts()
        likes = sum([post.likes() for post in posts], start=VKCommunity())
        users = likes.counter().most_common()[:10]
        return [
            {
                'id': user_id,
                'url': VKUser(user_id).url,
                'name': VKUser(user_id).name,
                'weight': count
            }
            for user_id, count in users
        ]

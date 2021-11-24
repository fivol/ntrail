import asyncio
import logging
import typing
from collections import Counter

from core import VKUser, IGUser, IGCommunity
from server.plugin.plugin import BasePlugin
from server.routes.vk.plugins.user import UserDescribePlugin
from worker.instagramscraper.exception.instagram_not_found_exception import InstagramNotFoundException

logger = logging.getLogger(__name__)


class FindInstagramPlugin(BasePlugin):
    name = 'find-instagram'

    def __init__(self, user, **kwargs):
        super(FindInstagramPlugin, self).__init__(**kwargs)
        self._user = user

    @classmethod
    async def _get_followers(cls, ig_username: str) -> typing.Optional[list]:
        try:
            ig = await IGUser.create(ig_username)
            return await ig.followers()
        except InstagramNotFoundException:
            return None

    async def response(self) -> typing.Optional[str]:
        own_instagram = await UserDescribePlugin(self._user).instagram()
        if own_instagram:
            return own_instagram
        friends = await self._user.friends()
        await friends.data()
        users = friends.objects()
        instagram_urls = list(filter(lambda x: isinstance(x, str), await asyncio.gather(
            *[
                UserDescribePlugin(user).instagram()
                for user in users
            ],
            return_exceptions=True
        )))
        followers = await asyncio.gather(*[
            self._get_followers(inst) for inst in instagram_urls
        ])
        followers = list(filter(bool, followers))
        followers_butch = Counter()
        print(len(followers))
        for user_followers in followers:
            if isinstance(followers, Exception):
                logger.error('Getting followers')
            elif isinstance(user_followers, IGCommunity):
                followers_butch += user_followers.counter()

        for account_id, count in followers_butch.most_common(1):
            user = IGUser(account_id)
            await user.data()
            return user.url

        return None

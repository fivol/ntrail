import asyncio
import logging
import typing
from collections import Counter, defaultdict

from core import VKUser, IGUser, IGCommunity
from server.plugin.plugin import BasePlugin, call_plugin
from server.routes.vk.features.name_compare import NameComparator
from server.routes.vk.plugins.user import UserDescribePlugin, VKUserPlugin
from worker.instagramscraper.exceptions import *

logger = logging.getLogger(__name__)


class VKFindInstagramPlugin(BasePlugin):
    name = 'find-instagram'
    namespace = 'vk'

    def __init__(self, user: VKUser, **kwargs):
        super(VKFindInstagramPlugin, self).__init__(**kwargs)
        self._user = user

    @classmethod
    async def _get_followers(cls, ig_username: str) -> typing.Optional[list]:
        try:
            ig = await IGUser.create(ig_username)
            return await ig.followers()
        except InstagramException:
            # TODO Process inst exception
            return None

    async def response(self) -> list[str]:
        own_instagram = await call_plugin(VKUserPlugin(self._user), 'instagram')
        if own_instagram:
            return [own_instagram]
        friends = await self._user.friends()
        await friends.data()
        users = friends.objects()
        pools = await friends.pools()
        user_pool = {}
        for i, pool in enumerate(pools):
            for user in pool:
                user_pool[user] = i

        ig_vk = list(filter(lambda x: isinstance(x[0], str), zip(await asyncio.gather(
            *[
                call_plugin(VKUserPlugin(user), 'instagram')
                for user in users
            ],
            return_exceptions=True
        ), friends.nodes)))
        followers = zip(await asyncio.gather(*[
            self._get_followers(ig_vk_pair[0]) for ig_vk_pair in ig_vk
        ]), map(lambda x: x[1], ig_vk))

        followers = list(filter(lambda x: bool(x[0]), followers))
        logger.debug('Parse %s instagram accounts to grep follower', len(followers))
        followers_butch = Counter()
        follower_score = defaultdict(set)
        for user_followers, vk_id in followers:
            for follower in user_followers:
                follower_score[follower].add(user_pool.get(vk_id))
            followers_butch += user_followers.counter()

        # With inter cluster cross selection
        best_followers = Counter({follower: len(clusters) for follower, clusters in follower_score.items()})
        best = best_followers.most_common(1)[0]
        target_users = []
        logger.debug("Most common by clusters IG candidate: %s", best)
        if best[1] > 1:
            target_users = [best[0]]

        # Counting best by name matching
        await self._user.data()
        best_by_name = NameComparator.best_match([self._user.screen_name, self._user.first_name, self._user.last_name],
                                                 [(x[0].username, x[0].full_name, x[0]) for x in
                                                  followers_butch.most_common()])
        target_users.append(best_by_name.most_common(1)[0][0][2])

        # Just most commonly come
        max_count = None
        for account_id, count in followers_butch.most_common(1):
            if not max_count or count == max_count:
                if account_id not in target_users:
                    target_users.append(account_id)
                max_count = count
            else:
                break
        logger.debug('Most common iG candidate - count: %s, len: %s', max_count, target_users)
        return list([user.url for user in target_users])

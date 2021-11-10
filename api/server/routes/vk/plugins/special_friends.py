from collections import defaultdict
from pprint import pprint

from core import VKUser, VKCommunity
from server.plugin.plugin import BasePlugin
from worker import VkMethods
from server.routes.vk.plugins.representer import UsersRepresentation


class SpecialFriendsPlugin(BasePlugin):
    name = 'special-friends'

    def __init__(self, user: VKUser, **kwargs):
        super(SpecialFriendsPlugin, self).__init__(**kwargs)
        self._user = user

    async def response(self) -> list:
        result_count = 5
        friends = await self._user.friends()
        graph = await friends.graph()
        pools = await friends.pools()
        node_pool = {}
        pool_interaction_weight = defaultdict(dict)
        for i, pool in enumerate(pools):
            for node in pool:
                node_pool[node] = i
        for i, pool in enumerate(pools):
            for node in pool:
                for mate in graph[node]:
                    mate_pool = node_pool[mate]
                    if mate_pool == i:
                        continue
                    pool_interaction_weight[i][mate_pool] = pool_interaction_weight[i].get(mate_pool, 0) + 1

        node_cross_score = defaultdict(int)
        for node in graph:
            for friend in graph[node]:
                if node_pool[node] == node_pool[friend]:
                    continue
                node_cross_score[node] += 1 / pool_interaction_weight[node_pool[node]][node_pool[friend]] ** 1.4

        common_friends = map(lambda item: (item[1], item[0]), node_cross_score.items())
        common_friends = sorted(common_friends, reverse=True)[:result_count]
        common_friends_comm = VKCommunity(list(map(lambda x: x[1], common_friends)))
        representation = await UsersRepresentation.represent(common_friends_comm)
        return [
            {
                **item,
                'weight': weight[0]
            }
            for weight, item in zip(common_friends, representation)
        ]

import typing
from collections import defaultdict
from pprint import pprint

from core import VKUser, VKCommunity
from server.plugin.plugin import BasePlugin
from worker import VkMethods
from server.routes.vk.plugins.representer import UsersRepresentation


class ValueScore:
    def __init__(self, value):
        object.__setattr__(self, 'value', value)
        object.__setattr__(self, 'data', {})

    def __getattr__(self, item):
        return self.data.get(item, 0)

    def __setattr__(self, key, value):
        self.data[key] = value

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __iter__(self):
        return self.data

    def __repr__(self):
        return repr(self.data)


class ScoredValues:
    def __init__(self, items: typing.Optional[list] = None):
        self.items = {}
        self.ordered_items = items or []

    def __getitem__(self, item):
        if item not in self.items:
            self.items[item] = ValueScore(item)
        return self.items[item]

    def __iter__(self):
        if self.items:
            return iter(self.items.values())
        return iter(self.ordered_items)

    def sorted(self, key: str = None, func=None):
        if key:
            func = lambda item: item[key]
        return ScoredValues(sorted(self.items.values(), key=func, reverse=True))

    def add_key(self, name: str, func):
        for score in self:
            setattr(score, name, func(score))

    def select(self, count):
        return ScoredValues(self.ordered_items[:count])

    def values(self):
        return list(map(lambda item: item.value, iter(self)))

    def __repr__(self):
        if self.items:
            return repr(self.items)
        return repr(self.ordered_items)


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
        cluster_size = defaultdict(int)
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

        nodes_score = ScoredValues()
        for node in graph:
            for friend in graph[node]:
                if node_pool[node] == node_pool[friend]:
                    continue
                nodes_score[node].cluster_size = len(pools[node_pool[node]])
                nodes_score[node].cross += 1 / pool_interaction_weight[node_pool[node]][node_pool[friend]] ** 1.4

        nodes_score.add_key('target', lambda item: item.cross + 0 * item.cluster_size)
        scored = nodes_score.sorted('target').select(result_count)
        representation = await UsersRepresentation.represent(VKCommunity(scored.values()))
        return [
            {
                **item,
                'weight': round(score['target'], 4)
            }
            for score, item in zip(scored, representation)
        ]

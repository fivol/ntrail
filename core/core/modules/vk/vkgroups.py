import asyncio
import logging

from core.modules.vk.vkgroup import VKGroup
from pycommon.decors import cache_method_ignore_args
from worker import VKMethods
from more_itertools import unique_everseen

from collections import Counter
import networkx as nx
import math

from core.module.connected_entities import ConnectedEntities

logger = logging.getLogger()


class VKGroups(ConnectedEntities):
    _single_media_cls = VKGroup

    def __init__(self, groups=None, target=None, source=None, **kwargs):
        super().__init__()
        self._target = target
        self._source = source
        self._main = None

        if isinstance(groups, Counter):
            self._counter = groups
            self.nodes = list(groups)
        elif isinstance(groups, list) or isinstance(groups, set):
            groups = list(unique_everseen(groups))
            if not groups:
                return
            if isinstance(groups[0], int):
                self.nodes = groups
            else:
                raise ValueError('Unknown nodes type for groups')

        else:
            raise TypeError('Unknown group init type')

    def split_components(self):
        return sorted([VKGroups(comp) for comp in nx.connected_components(self.graph)],
                      key=lambda x: -len(x.objects))

    def only_valid(self):
        return VKGroups([group for group in self.objects() if group.valid])

    def members(self):
        members_ids = []
        for group in self.nodes:
            members_ids += self.get_random_group_members(group, k=100)[:100]

        from .vkcommunity import VKCommunity
        return VKCommunity(members_ids, target='members', main=self.objects()[0])

    async def data(self) -> list:
        return await VKMethods.groups_ids(self.nodes)

    async def select_type(self, type_name):
        return VKGroups([group['id'] for group in await self.data() if group['type'] == type_name])

    @cache_method_ignore_args
    async def graph(self, members_count=1000, threshold=0.005) -> nx.Graph:
        graph = nx.Graph()
        graph.add_nodes_from(self.nodes)
        groups = self.objects()
        members = await asyncio.gather(*[
            group.members(count=members_count) for group in groups
        ], return_exceptions=True)
        members = {
            group.id: members_
            for group, members_ in zip(groups, members) if not isinstance(members_, Exception)
        }

        for num, i in enumerate(self.nodes):
            for j in self.nodes[num + 1:]:
                if i in members and j in members:
                    weight = self._groups_connectedness(members[i], members[j])
                    if weight > threshold:
                        graph.add_edge(i, j, weight=weight)
        return graph

    @classmethod
    def _groups_connectedness(cls, c1, c2):
        return len(set(c1.nodes).intersection(set(c2.nodes))) / min(len(c1), len(c2))

    def links_graph(self):
        groups_data = self.full_data
        groups_names_dict = dict_from_dicts(groups_data, 'name')
        g = nx.Graph()
        for group_name, group_data in groups_names_dict.items():
            g.add_node(group_data['id'])
            if 'links' in group_data:
                for link in group_data['links']:
                    link_name = link['name']
                    link_group = groups_names_dict.get(link_name, None)

                    if link_group:
                        g.add_edge(group_data['id'], link_group['id'])
        return g

    def reverse(self):
        return self.order('reverse')

    async def order(self, order_type='smart'):
        if order_type == 'smart':
            await self.data()
            return VKGroups(
                Counter(
                    {
                        group.id: self.counter[group.id] / (math.log(group.short_data.get('members_count', 10) + 1))
                        for group in self.objects()
                    }
                )
            )
        if order_type == 'popular':
            await self.data()
            return VKGroups(
                Counter(
                    dict(
                        [(group.id, group.short_data.get('members_count', 10))
                         for group in self.objects()]
                    )
                )
            )
        if order_type == 'reverse':
            return VKGroups(Counter(dict([(item, 1 / count) for item, count in self.counter.most_common()])))

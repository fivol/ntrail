import random
import re
from collections import Counter

import networkx as nx

from core.module.connected_entities import ConnectedEntities
from pycommon.decors import cache_method_ignore_args
from worker import VKMethods
from core.modules.vk.vkgroup import VKGroup
from core.modules.vk.vkgroups import VKGroups
from core.modules.vk.vkuser import VKUser


class VKCommunity(ConnectedEntities):
    _single_media_cls = VKUser

    def __init__(self, users=None, main=None, target=None, target_value=None, **kwargs):
        super().__init__()
        self.target_value = target_value
        if isinstance(users, set):
            users = list(users)
        assert main is None or isinstance(main, VKUser) or isinstance(main, VKGroup), main
        self.main = main
        self.target = target
        if not users:
            return
        if isinstance(users, Counter):
            self._counter = users
            self.nodes = list(users)
        elif isinstance(users, list):
            if users:
                if isinstance(users[0], VKUser):
                    self.nodes = [user.id for user in users]
                elif isinstance(users[0], int):
                    self.nodes = users
                elif isinstance(users[0], dict):
                    self._data = users
                    self.nodes = [user['id'] for user in users]
                else:
                    raise TypeError('user instance must be int or string, but' + str(type(users[0])))
            self._counter = Counter(self.nodes)
            self.nodes = list(set(self.nodes))
        elif not (users is None):
            raise TypeError('Wrong users type: {}'.format(type(users)))

    @staticmethod
    def _parse_usernames(usernames_string):
        usernames = re.findall(r'vk.com/([0-9a-z._]+)', usernames_string)
        return list(set(usernames))

    def deactivated(self):
        return VKCommunity([user for user in self.objects() if not user.valid], clear=False)

    async def groups(self):
        all_groups_ids = sum(
            filter(
                lambda x: isinstance(x, list), await VKMethods.groups.map(self.nodes)),
            [])
        return VKGroups(all_groups_ids)

    @cache_method_ignore_args
    async def data(self) -> list:
        return await VKMethods.users(self.nodes)

    async def friends(self):
        users_friends = await VKMethods.friends(self.nodes)
        users_friends += [self.nodes]
        return VKCommunity(sum(filter(lambda x: isinstance(x, list), users_friends), []))

    @cache_method_ignore_args
    async def graph(self):
        graph = nx.Graph()
        connections = await VKMethods.friends.map(self.nodes)
        friends = {
            node: conn
            for node, conn in zip(self.nodes, connections) if not isinstance(conn, Exception)
        }
        for node, node_friends in friends.items():
            for friend in node_friends:
                if friend in friends:
                    graph.add_edge(node, friend)

        return graph

    async def only_valid(self):
        await self.preload()
        return VKCommunity(
            Counter({user.id: self.counter()[user.id] for user in self.objects() if await user.valid()})
        )

    @classmethod
    def random(cls, size):
        comm = VKCommunity()
        while comm.size < size:
            min_vkid = 1
            max_vkid = 420000000
            ids_list = random.sample(range(min_vkid, max_vkid), size * 2)
            comm = VKCommunity(list(ids_list)).only_valid().select(size)
        return comm

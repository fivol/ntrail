from baseapi import BaseAPI
from tools import once_property
from instuser import InstUser
import instagram
from collections import Counter
import networkx as nx
from instagram.entities import Account


class InstCommunity(BaseAPI):
    def __init__(self, users):
        if not users:
            self.nodes = []
            self.size = 0
            self.counter = Counter()
            return
        if isinstance(users, Counter):
            self.counter = users
            self.nodes = list(users)
        else:
            user0 = users[0]
            if isinstance(user0, InstUser):
                self.nodes = [user.username for user in users]
            elif isinstance(user0, str):
                self.nodes = users
            elif isinstance(user0, instagram.entities.Account):
                self.nodes = [node.username for node in users]
            else:
                raise TypeError('Wrong users type ' + str(type(users)))

            self.counter = Counter(self.nodes)
            self.nodes = list(self.counter)

        self.size = len(self.nodes)

    @once_property
    def users(self):
        return [InstUser(username) for username in self.nodes]

    def print(self, k=None):
        users = sorted(self.users, key=lambda x: -self.counter[x.username])
        if k:
            users = users[:k]

        self.get_objects_medias([Account(user.username) for user in users])
        for user in users:
            if self.counter[user.username] != 1:
                user.print(self.counter[user.username])
            else:
                user.print()

    def __add__(self, other):
        return InstCommunity(self.counter + other.counter)

    @once_property
    def valid_users(self):
        self.get_objects_medias([Account(username) for username in self.nodes])
        return InstCommunity([user for user in self.users if user.valid])

    def friends(self):
        return self.followers() + self.follows()

    @once_property
    def graph(self):
        g = nx.Graph()
        self.friends()
        g.add_nodes_from(self.nodes)
        for user in self.users:
            friends = user.friends().nodes
            if friends:
                g.add_edges_from([(user.username, friend) for friend in friends if friend in self.nodes])
        return g

    @once_property
    def short_info(self):
        return ''

    def followers(self):
        nodes = self.get_users_followers(self.nodes)
        nodes = sum(nodes, [])
        return InstCommunity(Counter(nodes))

    def follows(self):
        nodes = self.get_users_follows(self.nodes)
        nodes = sum(nodes, [])
        return InstCommunity(Counter(nodes))

    def common(self, k=-1, break_point=1):
        if k <= 0:
            return InstCommunity(Counter(dict(self.counter_top(self.counter.most_common(), break_point))))
        return InstCommunity(Counter(dict(self.counter.most_common(k))))



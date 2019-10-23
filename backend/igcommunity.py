from tools import once_property, timeit
from iguser import IGUser
import instagram
from collections import Counter
import networkx as nx
from instagram.entities import Account
from many_objects import ManyObjects


class IGCommunity(ManyObjects):
    def __init__(self, users):
        self.base_class = IGUser
        super().__init__()
        if not users:
            self.nodes = []
            self.size = 0
            self.counter = Counter()
            return
        if isinstance(users, Counter):
            self.counter = users
            self.nodes = list(users)
        elif isinstance(users, list):
            user0 = users[0]
            if isinstance(user0, IGUser):
                self.nodes = [user.username for user in users]
            elif isinstance(user0, str):
                self.nodes = users
            elif isinstance(user0, instagram.entities.Account):
                self.nodes = [node.username for node in users]
            else:
                raise TypeError('Wrong users type ' + str(type(users)))

            self.counter = Counter(self.nodes)
            self.nodes = list(self.counter)
        else:
            raise TypeError('Users must be Counter or list type')

        self.size = len(self.nodes)

    def load_media_data(self, users=None, full=False):
        if not users:
            users = self.objects
        self.get_objects_medias([Account(user.username) for user in users], full=full)

    @once_property
    def short_data(self):
        self.load_media_data(full=False)
        return [user.short_data for user in self.objects]

    @once_property
    def full_data(self):
        self.load_media_data(full=True)
        return [user.full_data for user in self.objects]

    def get_key_words(self):
        result = {}
        for data in self.short_data:
            name = data['full_name']
            username = data['username']
            if name:
                result[name] = data['username']
            names = name.split(' ')
            if len(names) > 1:
                if names[0] and names[1]:
                    result[f'{names[1]} {names[0]}'] = username
                if names[0]:
                    result[names[0]] = username
                if names[1]:
                    result[names[1]] = username
            result[username] = username
        return dict(result)

    @once_property
    def valid_users(self):
        self.get_objects_medias([Account(username) for username in self.nodes])
        return IGCommunity([user for user in self.objects if user.valid])

    def friends(self, include_self=False):
        friends_community = self.followers() + self.follows()
        if include_self:
            friends_community += self.__class__(self.nodes)
        return friends_community

    def get_connections(self, **kwargs):
        self.friends()
        return dict([(obj, obj.friends().nodes) for obj in self.objects])

    @once_property
    def short_info(self):
        return ''

    def followers(self):
        nodes = self.get_users_followers(self.nodes)
        nodes = sum(nodes, [])
        return IGCommunity(Counter(nodes))

    def follows(self):
        nodes = self.get_users_follows(self.nodes)
        nodes = sum(nodes, [])
        return IGCommunity(Counter(nodes))

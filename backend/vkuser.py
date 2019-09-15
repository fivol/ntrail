from baseapi import BaseAPI, once_property
import pickle
import matplotlib.pyplot as plt
import io
import numpy as np
import random


class VKUser(BaseAPI):
    def __init__(self, user, verbose=0):
        super().__init__(verbose)
        if isinstance(user, str):
            try:
                if len(user) < 3: raise Exception()
                self.vkid = int(user[2:])
            except:
                user = user.split('/')[-1]
                self.vkid = self.resolve_screen_name(user)['object_id']

        else:
            self.vkid = user

    @once_property
    def groups_ids(self):
        return self.get_user_groups(self.vkid)

    @once_property
    def groups(self):
        from groups_pool import GroupsPool
        groups = self.groups_ids
        return GroupsPool(groups)

    def get_groups_pools(self):
        return self.groups.split_components()

    @classmethod
    def get_random_user(cls):
        min_vkid = 1
        max_vkid = 420000000
        base = BaseAPI(verbose=0)
        ids_list = np.random.randint(min_vkid, max_vkid, size=5)
        users = [x for x in base.get_users(ids_list, full=True).values() if 'deactivated' not in x]
        if not users:
            return cls.get_random_user()
        return VKUser(users[0]['id'])

    @once_property
    def friends_ids(self):
        return self.get_user_friends(self.vkid)

    @once_property
    def short_data(self):
        return self.get_user(self.vkid)

    @once_property
    def full_data(self):
        return self.get_user(self.vkid, full=True)

    @property
    def name(self):
        return f"{self.short_data['first_name']} {self.short_data['last_name']}"

    @property
    def url(self):
        return f'https://vk.com/id{self.vkid}'

    @once_property
    def friends(self):
        from community import Community
        friends = set(self.friends_ids)
        friends.add(self.vkid)
        return Community(friends)

    def show_communities_graph(self):
        pass

    def get_communities(self, **kwargs):
        return self.friends.split(**kwargs)

    def print(self):
        print_string = f'{self.name} {self.vkid} {self.url}'
        print(print_string)

    def print_name(self):
        print(self.name)

    @once_property
    def params(self):
        pass

    def show_icon(self):
        user = self.short_data
        url = user['photo_200']
        a = io.imread(url)
        plt.figure(figsize=(1, 1))
        plt.axis('off')
        plt.imshow(a)
        plt.show()

    def save(self, file_name=None):
        if not file_name:
            file_name = f'users/{self.name} {self.vkid}'
        with open(file_name, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, file_name):
        with open(file_name, 'rb') as f:
            return pickle.load(f)

from one_object import OneObject
from tools import timeit, once_property
import matplotlib.pyplot as plt
import io
import numpy as np
from vkgroups import VKGroups
from glbal import logger


class VKUser(OneObject):
    def __init__(self, user):
        super().__init__()
        if not user:
            raise Exception('Empty name')
        if isinstance(user, str):
            try:
                self.id = int(user[2:])
            except:
                user = user.split('/')[-1]
                self.id = self.resolve_screen_name(user)['object_id']
        elif isinstance(user, int):
            self.id = user
        else:
            raise Exception('Wrong user type')
        self.pk = self.id

    def groups(self):
        return VKGroups(self.get_user_groups(self.id))

    @classmethod
    def generate_random(cls):
        from vkcommunity import VKCommunity
        return VKCommunity.generate_random(1).objects[0]

    @once_property
    def friends_ids(self):
        return self.get_user_friends(self.id)

    @once_property
    def short_data(self):
        return self.get_user(self.id, full=False)

    @once_property
    def full_data(self):
        return self.get_user(self.id, full=True)

    @property
    def name(self):
        return f"{self.short_data['first_name']} {self.short_data['last_name']}"

    @property
    def url(self):
        return f'https://vk.com/id{self.id}'

    def get_key_words(self):
        site_string = ' '.join([str(item) for key, item in self.full_data.items() if not key.startswith('photo')])
        sites = self.get_sites(site_string)
        sites_username = []
        for host, site in sites:
            try:
                if site.endswith('/'):
                    site = site[:-1]
                path_items = site.split('//')[1].split('/')
                if len(path_items) >= 2:
                    sites_username.append(path_items[-1])
            except:
                logger.exception('Fail to get username from site: %s', site)

        key_words = [
            self.name,
            self.full_data.get('first_name', None),
            self.full_data.get('last_name', None),
            self.full_data.get('screen_name', None),
            self.full_data.get('skype', None),
            self.full_data.get('livejournal', None),
            self.full_data.get('instagram', None),
            self.full_data.get('twitter', None),
            self.full_data.get('facebook', None),
            self.full_data.get('maiden_name', None),
            self.full_data.get('nickname', None),
            *sites_username
        ]
        key_words = list(filter(lambda x: bool(x), key_words))
        return key_words

    def friends(self):
        from vkcommunity import VKCommunity
        friends_ids = self.get_user_friends(self.id)
        friends_ids.append(self.id)
        return VKCommunity(friends_ids, main_user=self.id)

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

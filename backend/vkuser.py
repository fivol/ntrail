from baseapi import BaseAPI, once_property
import matplotlib.pyplot as plt
import io
import numpy as np
from groups_pool import GroupsPool


class VKUser(BaseAPI):
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

    @once_property
    def groups(self):
        return GroupsPool(self.get_user_groups(self.id))

    @classmethod
    def from_random(cls):
        min_id = 1
        max_id = 420000000
        base = BaseAPI(verbose=0)
        ids_list = np.random.randint(min_id, max_id, size=5)
        users = [x for x in base.get_users(ids_list, full=True).values() if 'deactivated' not in x]
        if not users:
            return cls.from_random()
        return VKUser(users[0]['id'])

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

    @once_property
    def friends(self):
        from community_pool import Community
        friends_ids = self.get_user_friends(self.id)
        friends_ids.append(self.id)
        return Community(friends_ids, main_user=self.id)

    @once_property
    def params(self):
        pass

    def print(self):
        print(f'{self.name}\t\t {self.url}')

    def show_icon(self):
        user = self.short_data
        url = user['photo_200']
        a = io.imread(url)
        plt.figure(figsize=(1, 1))
        plt.axis('off')
        plt.imshow(a)
        plt.show()

    def __hash__(self):
        return hash(self.id)

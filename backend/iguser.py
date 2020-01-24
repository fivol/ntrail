from tools import once_property
from instagram.entities import Account
from glbal import logger
from one_object import OneObject


class IGUser(OneObject):
    def __init__(self, user):
        if isinstance(user, str):
            if user.endswith('/'):
                user = user[:-1]
            username = user.split('/')[-1]
            self.username = username
        elif isinstance(user, Account):
            self.username = user.username
        else:
            raise TypeError(f'Wrong user type: {type(user)}, {user}')

        self.id = self.username
        super().__init__()

    @once_property
    def url(self):
        return f'https://instagram.com/{self.username}/'

    def get_account(self, full=False):
        account = Account(self.username)
        return self.get_media(account, full=full)

    @property
    def name(self):
        return self.short_data['full_name']

    @once_property
    def short_data(self):
        ac = self.get_account(full=False)
        return {
            'full_name': ac.full_name,
            'id': ac.id,
            'is_verified': ac.is_verified,
            'profile_pic_url': ac.profile_pic_url,
            'username': ac.username
        }

    @once_property
    def full_data(self):
        ac = self.get_account(full=True)
        data = {
            'biography': ac.biography,
            'country_block': ac.country_block,
            'fb_page': ac.fb_page,
            'followers_count': ac.followers_count,
            'follows_count': ac.follows_count,
            'full_name': ac.full_name,
            'id': ac.id,
            'is_private': ac.is_private,
            'is_verified': ac.is_verified,
            'media_count': ac.media_count,
            'profile_pic_url': ac.profile_pic_url,
            'profile_pic_url_hd': ac.profile_pic_url_hd,
            'username': ac.username,
        }
        return data

    def print(self, *args, **kwargs):
        if not self.valid:
            print(f'ACCOUNT DOES NOT EXIST: {self.username}')
        else:
            super().print(*args, **kwargs)

    def followers(self, count=300):
        from igcommunity import IGCommunity
        nodes = self.get_followers(self.username, count=count)
        return IGCommunity(nodes)

    def follows(self, count=300):
        from igcommunity import IGCommunity
        nodes = self.get_follows(self.username, count=count)
        return IGCommunity(nodes)

    @property
    def is_private(self):
        return self.full_data['is_private']

    def friends(self):
        from igcommunity import IGCommunity
        return self.follows() + self.followers() + IGCommunity([self.username])

    @once_property
    def valid(self):
        return not self.get_account() is None


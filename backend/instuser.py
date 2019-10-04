from tools import once_property
from baseapi import BaseAPI
from instagram.entities import Account
from glbal import logger


class InstUser(BaseAPI):
    def __init__(self, user):
        if isinstance(user, str):
            if user.endswith('/'):
                user = user[:-1]
            username = user.split('/')[-1]
            self.username = username
        elif isinstance(user, Account):
            self.account_ = user
            self.username = user.username
        else:
            raise TypeError(f'Wrong user type: {type(user)}, {user}')

        super().__init__()

    @once_property
    def url(self):
        return f'https://instagram.com/{self.username}/'

    @once_property
    def account(self):
        account = Account(self.username)
        return self.get_media(account)

    @property
    def name(self):
        return self.account.full_name

    @property
    def follows_count(self):
        return self.account.follows_count

    @property
    def followers_count(self):
        return self.account.followers_count

    def print(self, extra_data=''):
        if self.valid:
            name = f'{self.username} {self.name} {extra_data}'
            name = name + ' ' * max(25 - len(name), 1)
            print(f'{name} {self.url}')
        else:
            print(f'ACCOUNT DOES NOT EXIST: {self.username}')

    def followers(self, count=300):
        from instcommunity import InstCommunity
        nodes = self.get_followers(self.username, count=count)
        return InstCommunity(nodes)

    def follows(self, count=300):
        from instcommunity import InstCommunity
        nodes = self.get_follows(self.username, count=count)
        return InstCommunity(nodes)

    def friends(self):
        return self.follows() + self.followers()

    @once_property
    def valid(self):
        return not self.account is None




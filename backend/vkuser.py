from one_object import OneObject
from tools import once_property, valid_object_method, get_sites
import matplotlib.pyplot as plt
import io
import re
from vkgroups import VKGroups
from glbal import logger
from constants import QUERY_RESULT_INVALID_ID, ACCOUNT_STATUS_BANNED, ACCOUNT_STATUS_DELETED, \
    ACCOUNT_STATUS_PRIVATE, ACCOUNT_STATUS_ABSENT, ACCOUNT_STATUS_VALID, ACCOUNT_STATUS_PUBLIC
from vkapi import VKAPI


class VKUser(OneObject, VKAPI):

    @staticmethod
    def me():
        return VKUser('boris2000n')

    @staticmethod
    def alex():
        return VKUser('jolex009')

    @staticmethod
    def petr():
        return VKUser('p.volnov')

    @staticmethod
    def kate():
        return VKUser('katya11111')

    def __init__(self, user):
        super().__init__()
        self.status = None
        self.id = None

        if isinstance(user, str):
            if not user:
                self.status = ACCOUNT_STATUS_ABSENT
            else:
                username = VKUser.get_username(user)
                user_dict = self.resolve_screen_name(username)
                if not isinstance(user_dict, dict):
                    logger.info('VKUser username does not exist "%s"', username)
                    self.status = ACCOUNT_STATUS_ABSENT
                elif not user_dict['type'] == 'user':
                    logger.info('VKUser username type is "%s"', user_dict['type'])
                    self.status = ACCOUNT_STATUS_ABSENT
                else:
                    self.id = user_dict['object_id']
        elif isinstance(user, int):
            self.id = user
        else:
            raise TypeError(f'VKUser "{user}" type is {type(user)}')
        self.pk = self.id

    @staticmethod
    def get_username(url):
        url = url.lower()
        if re.fullmatch(r'[0-9a-z._]+', url):
            return url
        from vkcommunity import VKCommunity
        usernames = VKCommunity.parse_usernames(url)
        if not usernames:
            return None
        return usernames[0]

    def check_status(self):
        if not self.status:
            user_data = self.short_data
            if isinstance(user_data, str):
                if user_data == QUERY_RESULT_INVALID_ID:
                    self.status = ACCOUNT_STATUS_ABSENT
                else:
                    raise ValueError('VKUser short data have unknown value:', user_data)
            elif isinstance(user_data, dict):
                if 'deactivated' in user_data:
                    deactivated_status = user_data['deactivated']
                    if deactivated_status == 'deleted':
                        self.status = ACCOUNT_STATUS_DELETED
                    elif deactivated_status == 'banned':
                        self.status = ACCOUNT_STATUS_BANNED
                    else:
                        logger.warning('Unknown reason for user account deactivation: %s', deactivated_status)
                        self.status = ACCOUNT_STATUS_DELETED
                elif user_data['is_closed']:
                    self.status = ACCOUNT_STATUS_PRIVATE
                else:
                    self.status = ACCOUNT_STATUS_PUBLIC
            else:
                raise TypeError('VKUser short data wrong type:', user_data)
        assert bool(self.status)
        return self.status

    @once_property
    def valid(self):
        status = self.check_status()
        assert not (status is None), status
        return status == ACCOUNT_STATUS_VALID or \
               status == ACCOUNT_STATUS_PUBLIC or \
               status == ACCOUNT_STATUS_PRIVATE

    @valid_object_method
    def groups(self):
        return VKGroups(self.get_user_groups(self.id))

    @classmethod
    def generate_random(cls):
        from vkcommunity import VKCommunity
        return VKCommunity.generate_random(1).objects[0]

    @once_property
    def short_data(self):
        return self.get_user(self.id, full=False)

    @once_property
    def full_data(self):
        return self.get_user(self.id, full=True)

    @property
    @valid_object_method
    def name(self):
        return f"{self.short_data['first_name']} {self.short_data['last_name']}"

    @property
    @valid_object_method
    def url(self):
        return f'https://vk.com/id{self.id}'

    @valid_object_method
    def get_key_words(self):
        site_string = ' '.join([str(item) for key, item in self.full_data.items() if not key.startswith('photo')])
        sites = get_sites(site_string)
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

    @valid_object_method
    def friends(self):
        from vkcommunity import VKCommunity
        friends_ids = self.get_user_friends(self.id)
        friends_ids.append(self.id)
        return VKCommunity(friends_ids, main_user=self, clear=True)

    @once_property
    @valid_object_method
    def params(self):
        pass

    @valid_object_method
    def show_icon(self):
        user = self.short_data
        url = user['photo_200']
        a = io.imread(url)
        plt.figure(figsize=(1, 1))
        plt.axis('off')
        plt.imshow(a)
        plt.show()

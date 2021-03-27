from module_vk.vkgroups import VKGroups
from ntmodule.one_object_represent import OneObjectRepresent
from ntmodule.tools import once_property, valid_object_method, get_sites
import matplotlib.pyplot as plt
import io
import re
from glbal import logger
from apimodule_vk.vkapi import VKAPI
from module_vk.vkphoto import VKPhotos, VKAlbums
from ntapimodule.api_errors import APIError, INVALID_ID_ERROR
from constants import ACCOUNT_STATUS_BANNED, ACCOUNT_STATUS_DELETED, \
    ACCOUNT_STATUS_PRIVATE, ACCOUNT_STATUS_ABSENT, \
    ACCOUNT_STATUS_VALID, ACCOUNT_STATUS_PUBLIC
from module_vk.vkpost import VKPosts


class VKUser(VKAPI, OneObjectRepresent):
    id_prefix = 'vku_'
    available_attributes = ['friends', 'follows', 'followers', 'groups']

    @staticmethod
    def me():
        return VKUser('boris2000n')

    def __init__(self, user, **kwargs):
        super().__init__()
        # print(user)
        self.id = None
        self.status = None

        if isinstance(user, list):
            if len(user) > 1:
                raise ValueError(f'User list length = {len(user)}. Must be 1')
            user = user[0]

        if isinstance(user, str):
            if not user:
                self.status = ACCOUNT_STATUS_ABSENT
            elif user.startswith(self.id_prefix):
                self.id = int(user[4:])
            else:
                username = VKUser.get_username(user)
                user_dict = self.resolve_screen_name(username)
                if not isinstance(user_dict, dict):
                    logger.info('VKUser username does not exist "%s"', username)
                    self.status = ACCOUNT_STATUS_ABSENT
                elif user_dict.get('type') == 'user':
                    self.id = user_dict.get('object_id')
                else:
                    logger.info('VKUser username type is "%s"', user_dict.get('type'))
                    self.status = ACCOUNT_STATUS_ABSENT
        elif isinstance(user, int):
            if user < 0:
                raise ValueError('User id < 0', user)
            self.id = user

        elif isinstance(user, dict):
            if 'id' not in user:
                raise ValueError('Wrong user dict')
            self.id = user['id']
            self.full_data_ = user
        else:
            raise TypeError(f'VKUser {user} type is {type(user)}')

    @staticmethod
    def get_username(url):
        url = url.lower()
        if re.fullmatch(r'[0-9a-z._]+', url):
            return url
        from module_vk.vkcommunity import VKCommunity
        usernames = VKCommunity.parse_usernames(url)
        if not usernames:
            return None
        return usernames[0]

    @valid_object_method
    def photos(self):
        return VKPhotos(self.get_all_photos(self.id))

    @valid_object_method
    def user_photos(self):
        return VKPhotos(self.get_photos_with_user(self.id))

    @valid_object_method
    def albums(self):
        return VKAlbums(self.get_albums(self.id))

    def check_status(self):
        if not self.status:
            user_data = self.short_data
            if APIError.is_error(user_data):
                if APIError(user_data).code == INVALID_ID_ERROR:
                    self.status = ACCOUNT_STATUS_ABSENT
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
                elif user_data.get('is_closed', False):
                    self.status = ACCOUNT_STATUS_PRIVATE
                else:
                    self.status = ACCOUNT_STATUS_PUBLIC
            else:
                raise TypeError('VKUser short data wrong type:', type(user_data), user_data)
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
    def followers(self):
        from module_vk.vkcommunity import VKCommunity
        followers = self.get_user_followers(self.id)
        assert isinstance(followers, list)
        return VKCommunity(followers)

    @valid_object_method
    def follows(self):
        from module_vk.vkcommunity import VKCommunity
        subscriptions = self.get_user_subscriptions(self.id)
        assert isinstance(subscriptions, list)
        return VKCommunity(subscriptions)

    @valid_object_method
    def groups(self):
        return VKGroups(self.get_user_groups(self.id), source=self).order()

    @classmethod
    def generate_random(cls):
        from module_vk.vkcommunity import VKCommunity
        return VKCommunity.generate_random(1).objects[0]

    @once_property
    def short_data(self):
        return self.full_data

    @once_property
    def full_data(self):
        return self.get_user(self.id, full=True)

    def get_full_data(self, force):
        return self.get_user(self.id, full=True, force=force)

    @valid_object_method
    def posts(self):
        return VKPosts(self.get_user_posts(self.id))

    @property
    def name(self):
        return f"{self.short_data['first_name']} {self.short_data['last_name']}"

    @property
    def url(self):
        return f'https://vk.com/id{self.id}'

    def preload(self, force=False):
        self.get_full_data(force)

    @classmethod
    def parse_id(cls, id_):
        if not id_.startswith(VKUser.id_prefix):
            return None
        return int(id_[len(VKUser.id_prefix):])


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
        from module_vk.vkcommunity import VKCommunity
        friends_ids = self.get_user_friends(self.id)
        friends_ids.append(self.id)
        return VKCommunity(friends_ids, main=self, target='friends')

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

    def get_entity(self):
        response = {
            'id': self.get_id(),
            'accessStatus': self.check_status(),
        }
        if not self.valid:
            return {
                **response,
                'url': self.url,
                'img': 'https://vk.com/images/deactivated_100.png?ava=1',
                'name': 'Пользователь не валиден',
                'valid': False,
                'properties': {
                    'color': 'black',
                    'weight': 0,
                    'connections': [],
                }
            }
        return {
            **response,
            'url': self.url,
            'img': self.full_data.get('photo_100', 'https://vk.com/images/camera_100.png?ava=1'),
            'name': self.name,
            'username': self.full_data.get("screen_name", 'id' + str(self.id)),
            'nativeID': self.id,
            'valid': True,
            'verified': self.full_data.get('verified', False),
            'accessStatus': self.check_status(),
            'private': self.check_status() == ACCOUNT_STATUS_PRIVATE,
            'properties': {
                'color': 'blue' if self.full_data.get('sex', 2) == 2 else 'red',
                'weight': 1,
                'connections': []
            }
        }

    def get_params(self):
        return {
            'baseType': 'users',
            'service': 'vk',
            'type': 'user',
            'fullEntitiesCount': 1,
            'id': self.hash,
            'name': self.full_data['first_name'] if self.valid else 'Не валиден',
            'query': f'GET vk.user {self.full_data["screen_name"]}' if self.valid else ''
        }

    # def represent(self, force=False):
    #     if not self.valid:
    #         raise QueryDataException('такого пользователя не существует или страница более не валидна')
    #
    #     self.preload(force=force)
    #     return {
    #         'clusters': {
    #             'items': [
    #                 {
    #                     'properties': self.get_properties(),
    #                     'params': self.get_params(),
    #                     'entities': {
    #                         'items': [self.get_entity()],
    #                         'connections': []
    #                     },
    #                     'id': self.hash,
    #                     'actions': [
    #                         {
    #                             'id': 'friends',
    #                             'name': 'Получить друзей',
    #                             'act': 'append',
    #                             'value': 'friends'
    #                         },
    #                         {
    #                             'id': 'friends',
    #                             'name': 'Получить группы',
    #                             'act': 'append',
    #                             'value': 'groups'
    #                         },
    #                     ]
    #                 }
    #             ],
    #             # 'mainID': self.get_id()
    #         }
    #     }


from module_vk.vkcommunity import VKCommunity
VKUser.many_objects_class = VKCommunity

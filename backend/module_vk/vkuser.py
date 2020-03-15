import time

from one_object import OneObject
from tools import once_property, valid_object_method, get_sites, to_string_time_period
import matplotlib.pyplot as plt
import io
import re
from module_k.vkgroup import VKGroups
from glbal import logger
from module_k.vkapi import VKAPI
from module_k.vkphoto import VKPhotos, VKAlbums
from errors.api_errors import APIError, INVALID_ID_ERROR
from constants import ACCOUNT_STATUS_BANNED, ACCOUNT_STATUS_DELETED, \
    ACCOUNT_STATUS_PRIVATE, ACCOUNT_STATUS_ABSENT, \
    ACCOUNT_STATUS_VALID, ACCOUNT_STATUS_PUBLIC
from module_k.vkpost import VKPosts


class VKUser(OneObject, VKAPI):
    id_prefix = 'vku_'
    available_attributes = ['friends', 'follows', 'followers']

    @staticmethod
    def me():
        return VKUser('boris2000n')

    def __init__(self, user, **kwargs):
        super().__init__()
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
                print(user_dict)
                if not isinstance(user_dict, dict):
                    logger.info('VKUser username does not exist "%s"', username)
                    self.status = ACCOUNT_STATUS_ABSENT
                elif not user_dict['type'] == 'user':
                    logger.info('VKUser username type is "%s"', user_dict['type'])
                    self.status = ACCOUNT_STATUS_ABSENT
                else:
                    self.id = user_dict['object_id']
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
        from module_k.vkcommunity import VKCommunity
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
                raise TypeError('VKUser short data wrong type:', type(user_data))
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
        from module_k.vkcommunity import VKCommunity
        followers = self.get_user_followers(self.id)
        assert isinstance(followers, list)
        return VKCommunity(followers)

    @valid_object_method
    def follows(self):
        from module_k.vkcommunity import VKCommunity
        subscriptions = self.get_user_subscriptions(self.id)
        assert isinstance(subscriptions, list)
        return VKCommunity(subscriptions)

    @valid_object_method
    def groups(self):
        return VKGroups(self.get_user_groups(self.id))

    @classmethod
    def generate_random(cls):
        from module_k.vkcommunity import VKCommunity
        return VKCommunity.generate_random(1).objects[0]

    @once_property
    def short_data(self):
        return self.full_data
        # return self.get_user(self.id, full=False)

    @once_property
    def full_data(self):
        return self.get_user(self.id, full=True)

    def get_full_data(self, force):
        return self.get_user(self.id, full=True, force=force)

    @valid_object_method
    def posts(self):
        return VKPosts(self.get_user_posts(self.id))

    @property
    @valid_object_method
    def name(self):
        return f"{self.short_data['first_name']} {self.short_data['last_name']}"

    @property
    def url(self):
        return f'https://vk.com/id{self.id}'

    def preload(self, force=False):
        self.get_full_data(force)

    @classmethod
    def gen_id(cls, plain_id):
        if isinstance(plain_id, str) and plain_id.startswith(cls.id_prefix):
            return plain_id
        return cls.id_prefix + str(plain_id)

    @classmethod
    def parse_id(cls, id_):
        if not id_.startswith(VKUser.id_prefix):
            return None
        return int(id_[len(VKUser.id_prefix):])

    def get_id(self):
        return self.gen_id(self.id)

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
        from module_k.vkcommunity import VKCommunity
        friends_ids = self.get_user_friends(self.id)
        friends_ids.append(self.id)
        return VKCommunity(friends_ids, main_user=self, target='friends')

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

    def get_interesting_properties(self):
        return [
            {
                'name': 'Интересное свойство 1',
                'value': '23',
                'id': 52315,
                'idAll': 1
            },
            {
                'name': "Средний возраст",
                'value': "19.6",
                'type': "order",
                'id': 53124312,
            },
            {
                'name': "Максимальное число подписчиков",
                'value': "3567",
                'type': "order",
                'id': 5435325,
            },
            {
                'name': "Школа",
                'value': "СУНЦ МГУ",
                'confidence': 0.7,
                'type': "show",
                'id': 41325132
            }
        ]

    def get_important_properties(self):
        if not self.valid:
            return []
        return [
            {
                'name': "Количество",
                'value': "1",
                'id': 166
            },
            {
                'name': "Пол",
                'value': 'Мужской' if self.full_data['sex'] == 2 else 'Женский',
                'id': 42341
            },
            {
                'name': "Онлайн",
                'value': 'В сети' if self.full_data['online'] else to_string_time_period(
                    time.time() - self.full_data['last_seen']['time']
                ) + ' назад',
                'id': 16153
            }]

    def get_all_properties(self):
        return [
            {
                'name': "Возраст",
                'id': 0,
                'values': [
                    {
                        'name': "Минимальный",
                        'value': "14 лет",
                        'id': 1613
                    },
                    {
                        'name': "Средний",
                        'value': "18.1 год",
                        'id': 13513
                    },
                    {
                        'name': "Медианный",
                        'value': "17.4 года",
                        'id': 2715325
                    },
                    {
                        'name': "Максимальный",
                        'value': "26 лет",
                        'id': 3613351
                    }
                ]
            },
            {
                'name': "Количество друзей",
                'id': 1,
                'values': [
                    {
                        'name': "Минимальное",
                        'value': "4",
                        'id': 6153
                    },
                    {
                        'name': "Среднее",
                        'value': "89",
                        'id': 11432
                    },
                    {
                        'name': "Медианное",
                        'value': "56",
                        'id': 313212
                    },
                    {
                        'name': "Максимальное",
                        'value': "451",
                        'id': 41616
                    }
                ]
            }
        ]

    def get_properties(self):
        return {
            'all': self.get_all_properties(),
            'interesting': self.get_interesting_properties(),
            'important': self.get_important_properties()
        }

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
                    'sex': self.full_data['sex'] if self.valid else 2,
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
                'sex': self.full_data['sex'],
                'weight': 1,
                'connections': []
            }
        }

    def get_params(self):
        return {
            'baseType': 'users',
            'service': 'module_k',
            'type': 'user',
            'fullEntitiesCount': 1,
            'id': self.hash,
            'name': self.full_data['first_name'] if self.valid else 'Не валиден',
            'query': f'GET module_k.user {self.full_data["screen_name"]}' if self.valid else ''
        }

    def represent(self, force=False):
        from selective_query_execute import QueryDataException
        if not self.valid:
            raise QueryDataException('такого пользователя не существует или страница более не валидна')

        self.preload(force=force)
        return {
            'clusters': {
                'items': [
                    {
                        'properties': self.get_properties(),
                        'params': self.get_params(),
                        'entities': {
                            'items': [self.get_entity()],
                            'connections': []
                        },
                        'id': self.hash
                    }
                ],
                'connections': [],
                'mainID': self.get_id()
            }
        }

import logging
from functools import cache

from worker import VkMethods
from .vkgroups import VKGroups
from core.module.one_object_represent import OneObjectRepresent
from core.helpers.utils import once_property, valid_object_method, get_sites
# import matplotlib.pyplot as plt
import io
import re
from .vkphoto import VKPhotos, VKAlbums
from core.constants import AccountStatus
from .vkpost import VKPosts

logger = logging.getLogger('vk-user')


class VKUser(OneObjectRepresent):
    _id_prefix = 'vku_'
    available_attributes = ['friends', 'follows', 'followers', 'groups']

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
                self.status = AccountStatus.ABSENT
            elif user.startswith(self._id_prefix):
                self.id = int(user[4:])
            else:
                username = VKUser.extract_username(user)
                user_dict = VkMethods.resolve.sync(username)
                if not isinstance(user_dict, dict):
                    logger.info('VKUser username does not exist "%s"', username)
                    self.status = AccountStatus.ABSENT
                elif user_dict.get('type') == 'user':
                    self.id = user_dict.get('object_id')
                else:
                    logger.info('VKUser username type is "%s"', user_dict.get('type'))
                    self.status = AccountStatus.ABSENT
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
    def extract_username(url):
        url = url.lower()
        if re.fullmatch(r'[0-9a-z._]+', url):
            return url
        from .vkcommunity import VKCommunity
        usernames = VKCommunity.parse_usernames(url)
        if not usernames:
            return None
        return usernames[0]

    @valid_object_method
    def photos(self):
        return VKPhotos(VkMethods.photos.sync(owner_id=self.id))

    @valid_object_method
    def user_photos(self):
        return VKPhotos(self.get_photos_with_user(self.id))

    @valid_object_method
    def albums(self):
        return VKAlbums(self.get_albums(self.id))

    def check_status(self):
        if not self.status:
            user_data = self.data(full=False)
            # TODO Error handling
            # if APIError.is_error(user_data):
            #     if APIError(user_data).code == INVALID_ID_ERROR:
            #         self.status = AccountStatus.ABSENT
            if False:
                pass
            elif isinstance(user_data, dict):
                if 'deactivated' in user_data:
                    deactivated_status = user_data['deactivated']
                    if deactivated_status == 'deleted':
                        self.status = AccountStatus.DELETED
                    elif deactivated_status == 'banned':
                        self.status = AccountStatus.BANNED
                    else:
                        logger.warning('Unknown reason for user account deactivation: %s', deactivated_status)
                        self.status = AccountStatus.DELETED
                elif user_data.get('is_closed', False):
                    self.status = AccountStatus.PRIVATE
                else:
                    self.status = AccountStatus.PUBLIC
            else:
                raise TypeError('VKUser short data wrong type:', type(user_data), user_data)
        assert bool(self.status)
        return self.status

    @once_property
    def valid(self):
        status = self.check_status()
        assert not (status is None), status
        return status == AccountStatus.VALID or \
            status == AccountStatus.PUBLIC or \
            status == AccountStatus.PRIVATE

    @valid_object_method
    def followers(self):
        from .vkcommunity import VKCommunity
        followers = self.get_user_followers(self.id)
        assert isinstance(followers, list)
        return VKCommunity(followers)

    @valid_object_method
    def follows(self):
        from .vkcommunity import VKCommunity
        subscriptions = self.get_user_subscriptions(self.id)
        assert isinstance(subscriptions, list)
        return VKCommunity(subscriptions)

    @valid_object_method
    def groups(self):
        return VKGroups(self.get_user_groups(self.id), source=self).order()

    @classmethod
    def random(cls):
        from .vkcommunity import VKCommunity
        return VKCommunity.random(1).objects[0]

    @cache
    def data(self, force=False, full=True) -> dict:
        return VkMethods.users.sync([self.id], full=full)[0]

    def get_attribute(self, key: str, default=None):
        """Возвращает один из базовых параметров аккаунта по ключу
        Пытается минимизировать время, сначала обращается к
        урезанным данным"""
        return self.data(full=False).get(key, default) or self.data.get(key, default)

    @valid_object_method
    def posts(self):
        return VKPosts(self.get_user_posts(self.id))

    @property
    def name(self):
        return f"{self.data(full=False)['first_name']} {self.data(full=False)['last_name']}"

    @property
    def url(self):
        return f'https://vk.com/id{self.id}'

    @valid_object_method
    def get_key_words(self):
        site_string = ' '.join([str(item) for key, item in self.data().items() if not key.startswith('photo')])
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

        data = self.data()
        key_words = [
            self.name,
            data.get('first_name', None),
            data.get('last_name', None),
            data.get('screen_name', None),
            data.get('skype', None),
            data.get('livejournal', None),
            data.get('instagram', None),
            data.get('twitter', None),
            data.get('facebook', None),
            data.get('maiden_name', None),
            data.get('nickname', None),
            *sites_username
        ]
        key_words = list(filter(lambda x: bool(x), key_words))
        return key_words

    @valid_object_method
    def friends(self):
        from .vkcommunity import VKCommunity
        friend_ids = VkMethods.friends.sync(self.id)
        friend_ids.append(self.id)
        return VKCommunity(friend_ids, main=self, target='friends')

    @once_property
    @valid_object_method
    def params(self):
        pass

    @valid_object_method
    def show_icon(self):
        user = self.data(full=False)
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
            'img': self.data.get('photo_100', 'https://vk.com/images/camera_100.png?ava=1'),
            'name': self.name,
            'username': self.data.get("screen_name", 'id' + str(self.id)),
            'nativeID': self.id,
            'valid': True,
            'verified': self.data.get('verified', False),
            'accessStatus': self.check_status(),
            'private': self.check_status() == AccountStatus.PRIVATE,
            'properties': {
                'color': 'blue' if self.data.get('sex', 2) == 2 else 'red',
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
            'name': self.data['first_name'] if self.valid else 'Не валиден',
            'query': f'GET vk.user {self.data["screen_name"]}' if self.valid else ''
        }

    def __str__(self):
        return self.name

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


from .vkcommunity import VKCommunity

VKUser.many_objects_class = VKCommunity

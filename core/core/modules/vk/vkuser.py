import logging
from functools import cache
# import matplotlib.pyplot as plt
import io
import re

from core.modules.vk.vkphoto import VKPhotos
from core.constants import AccountStatus
from core.modules.vk.vkpost import VKPosts
from core.module.layers import public_object_method, valid_object_method
from core.modules.vk.vkgroups import VKGroups
from core.module.one_object_represent import OneObjectRepresent
from core.helpers.utils import get_sites
from parsers.vk.exceptions import VKErrorType

from worker.parsers.exceptions import ParserRealError
from worker import VkMethods, VKError

logger = logging.getLogger('vk-user')


class VKUser(OneObjectRepresent):
    _id_prefix = 'vku_'
    available_attributes = ['friends', 'follows', 'followers', 'groups']

    def __init__(self, user, **kwargs):
        super().__init__()
        self.id = None
        self._status = None

        if isinstance(user, list):
            if len(user) > 1:
                raise ValueError(f'User list length = {len(user)}. Must be 1')
            user = user[0]

        if isinstance(user, str):
            if not user:
                self._status = AccountStatus.ABSENT
            elif user.startswith(self._id_prefix):
                self.id = int(user[4:])
            else:
                username = VKUser._extract_username(user)
                user_dict = VkMethods.resolve.sync(username)
                if not isinstance(user_dict, dict):
                    logger.info('VKUser username does not exist "%s"', username)
                    self._status = AccountStatus.ABSENT
                elif user_dict.get('type') == 'user':
                    self.id = user_dict.get('object_id')
                else:
                    logger.info('VKUser username type is "%s"', user_dict.get('type'))
                    self._status = AccountStatus.ABSENT
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
    def _extract_username(url):
        url = url.lower()
        if re.fullmatch(r'[0-9a-z._]+', url):
            return url
        from .vkcommunity import VKCommunity
        usernames = VKCommunity.parse_usernames(url)
        if not usernames:
            return None
        return usernames[0]

    @public_object_method
    def photos(self):
        return VKPhotos(VkMethods.photos.sync(owner_id=self.id))

    def status(self):
        if self._status:
            return self._status
        data = self.data(full=False)
        # TODO Error handling
        if isinstance(data, VKError):
            if data.type == VKErrorType.UNKNOWN_USER:
                self._status = AccountStatus.ABSENT
        elif isinstance(data, dict):
            if 'deactivated' in data:
                deactivated_status = data['deactivated']
                if deactivated_status == 'deleted':
                    self._status = AccountStatus.DELETED
                elif deactivated_status == 'banned':
                    self._status = AccountStatus.BANNED
                else:
                    logger.warning('Unknown reason for user account deactivation: %s', deactivated_status)
                    self._status = AccountStatus.DELETED
            elif data.get('is_closed', False):
                self._status = AccountStatus.PRIVATE
            else:
                self._status = AccountStatus.PUBLIC
        else:
            raise TypeError('VKUser short data wrong type:', type(data), data)
        return self._status

    @property
    def valid(self):
        status = self.status()
        return status == AccountStatus.VALID or \
            status == AccountStatus.PUBLIC or \
            status == AccountStatus.PRIVATE

    @public_object_method
    def followers(self):
        from .vkcommunity import VKCommunity
        followers = VkMethods.followers.sync(self.id)
        return VKCommunity(followers)

    @public_object_method
    def subscriptions(self):
        from .vkcommunity import VKCommunity
        subscriptions = VkMethods.subscriptions(self.id)
        assert isinstance(subscriptions, list)
        return VKCommunity(subscriptions)

    @public_object_method
    def groups(self):
        return VKGroups(VkMethods.groups(self.id), source=self).order()

    @classmethod
    def random(cls):
        from .vkcommunity import VKCommunity
        return VKCommunity.random(1).objects[0]

    @cache
    def data(self, force=False, full=True) -> dict:
        return VkMethods.users.sync([self.id], full=full)[0]

    @public_object_method
    def posts(self):
        return VKPosts(VkMethods.posts(self.id))

    @property
    @public_object_method
    def name(self):
        return f"{self.data(full=False)['first_name']} {self.data(full=False)['last_name']}"

    @property
    def url(self):
        return f'https://vk.com/id{self.id}'

    @public_object_method
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

    @public_object_method
    def friends(self):
        from .vkcommunity import VKCommunity
        friend_ids = VkMethods.friends.sync(self.id)
        if isinstance(friend_ids, ParserRealError):
            return VKCommunity()
        friend_ids.append(self.id)
        return VKCommunity(friend_ids, main=self, target='friends')

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
            'accessStatus': self._status(),
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
            'img': self.data().get('photo_100', 'https://vk.com/images/camera_100.png?ava=1'),
            'name': self.name,
            'username': self.data().get("screen_name", 'id' + str(self.id)),
            'nativeID': self.id,
            'valid': True,
            'verified': self.data().get('verified', False),
            'accessStatus': self._status(),
            'private': self._status() == AccountStatus.PRIVATE,
            'properties': {
                'color': 'blue' if self.data().get('sex', 2) == 2 else 'red',
                'weight': 1,
                'connections': []
            }
        }

    def summary(self):
        return {
            'baseType': 'users',
            'service': 'vk',
            'type': 'user',
            'fullEntitiesCount': 1,
            'id': self.hash,
            'name': self.data()['first_name'] if self.valid else 'Не валиден',
            'query': f'GET vk.user {self.data()["screen_name"]}' if self.valid else ''
        }


from .vkcommunity import VKCommunity

VKUser._many_media_cls = VKCommunity

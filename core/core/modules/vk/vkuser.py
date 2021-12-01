from __future__ import annotations
import logging
import re

from core.helpers.utils import init_with_result
from core.modules.vk.vkphoto import VKPhotos
from core.constants import AccountStatus
from core.modules.vk.vkpost import VKPosts
from core.modules.vk.vkgroups import VKGroups
from pycommon.decors import cache_method_ignore_args
from worker.parsers.vk.exceptions import VKErrorType

from worker.parsers.exceptions import AccessApiException
from worker import VKMethods, VKError
from core.module.layers import public_object_method
from core.module.single_entity import SingleEntity

logger = logging.getLogger('vk-user')


class VKUser(SingleEntity):

    @classmethod
    async def create(cls, user) -> VKUser:
        status = None
        user_id = None
        if isinstance(user, str):
            if not user:
                status = AccountStatus.ABSENT
            else:
                username = VKUser._extract_username(user)
                user_dict = await VKMethods.resolve(username)
                if not isinstance(user_dict, dict):
                    logger.info('VKUser username does not exist "%s"', username)
                    status = AccountStatus.ABSENT
                elif user_dict.get('type') == 'user':
                    user_id = user_dict.get('object_id')
                else:
                    logger.info('VKUser username type is "%s"', user_dict.get('type'))
                    status = AccountStatus.ABSENT
        return cls(user=user_id, status=status)

    def __init__(self, user, status=None, **kwargs):
        super().__init__(**kwargs)
        self._status = status
        self.id = None
        self.screen_name = None
        self.first_name = None
        self.last_name = None
        self.sex = None
        if isinstance(user, int):
            self.id = user
        elif isinstance(user, dict):
            self.id = user['id']
            self._init(user)
            self._data = user
        elif user is not None:
            raise TypeError('Unknown user type', type(user))

    @staticmethod
    def _extract_username(url):
        url = url.lower()
        if re.fullmatch(r'[0-9a-zA-Z._]+', url):
            return url
        from .vkcommunity import VKCommunity
        usernames = VKCommunity._parse_usernames(url)
        if not usernames:
            return None
        return usernames[0]

    async def photos(self):
        return VKPhotos(await VKMethods.photos_all(owner_id=self.id, all=True))

    async def profile_photos(self):
        return VKPhotos(await VKMethods.photos(owner_id=self.id, album_id='profile', all_=True))

    async def wall_photos(self):
        return VKPhotos(await VKMethods.photos(owner_id=self.id, album_id='wall', all_=True))

    async def status(self):
        if self._status:
            return self._status
        data = await self.data()
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

    async def valid(self):
        status = await self.status()
        return status == AccountStatus.VALID or \
            status == AccountStatus.PUBLIC or \
            status == AccountStatus.PRIVATE

    def followers(self):
        from .vkcommunity import VKCommunity
        followers = VKMethods.followers.sync(self.id)
        return VKCommunity(followers)

    def subscriptions(self):
        from .vkcommunity import VKCommunity
        subscriptions = VKMethods.subscriptions(self.id)
        assert isinstance(subscriptions, list)
        return VKCommunity(subscriptions)

    async def groups(self):
        return VKGroups(await VKMethods.groups(self.id), source=self)

    @classmethod
    def random(cls):
        from .vkcommunity import VKCommunity
        return VKCommunity.random(1).objects[0]

    @cache_method_ignore_args
    @init_with_result
    async def data(self) -> dict:
        return (await VKMethods.users([self.id]))[0]

    @public_object_method
    async def posts(self, all_=False) -> VKPosts:
        return VKPosts(await VKMethods.posts(self.id, all_=all_))

    async def name(self):
        return f"{(await self.data())['first_name']} {(await self.data())['last_name']}"

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def url(self):
        return f'https://vk.com/id{self.id}'

    async def friends(self, include_self=False):
        from .vkcommunity import VKCommunity
        friend_ids = await VKMethods.friends(self.id)
        if isinstance(friend_ids, AccessApiException):
            return VKCommunity()
        if include_self:
            friend_ids.append(self.id)
        return VKCommunity(friend_ids, main=self, target='friends')

import logging
from functools import cache
import re

from core.modules.vk.vkphoto import VKPhotos
from core.constants import AccountStatus, NO_AVA_IMG
from core.modules.vk.vkpost import VKPosts
from core.modules.vk.vkgroups import VKGroups
from core.module.one_object_represent import OneObjectRepresent
from worker.parsers.vk.exceptions import VKErrorType

from worker.parsers.exceptions import ParserRealError
from worker import VkMethods, VKError
from ...module.layers import public_object_method

logger = logging.getLogger('vk-user')


class VKUser(OneObjectRepresent):

    @classmethod
    async def create(cls, user):
        status = None
        user_id = None
        if isinstance(user, str):
            if not user:
                status = AccountStatus.ABSENT
            else:
                username = VKUser._extract_username(user)
                user_dict = await VkMethods.resolve(username)
                if not isinstance(user_dict, dict):
                    logger.info('VKUser username does not exist "%s"', username)
                    status = AccountStatus.ABSENT
                elif user_dict.get('type') == 'user':
                    user_id = user_dict.get('object_id')
                else:
                    logger.info('VKUser username type is "%s"', user_dict.get('type'))
                    status = AccountStatus.ABSENT
        return cls(user_id=user_id, status=status)

    def __init__(self, user_id: int, status=None, **kwargs):
        super().__init__()
        self.id = user_id
        self._status = status
        assert isinstance(user_id, int)

    @staticmethod
    def _extract_username(url):
        url = url.lower()
        if re.fullmatch(r'[0-9a-z._]+', url):
            return url
        from .vkcommunity import VKCommunity
        usernames = VKCommunity._parse_usernames(url)
        if not usernames:
            return None
        return usernames[0]

    def photos(self):
        return VKPhotos(VkMethods.photos.sync(owner_id=self.id))

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
        followers = VkMethods.followers.sync(self.id)
        return VKCommunity(followers)

    def subscriptions(self):
        from .vkcommunity import VKCommunity
        subscriptions = VkMethods.subscriptions(self.id)
        assert isinstance(subscriptions, list)
        return VKCommunity(subscriptions)

    def groups(self):
        return VKGroups(VkMethods.groups(self.id), source=self).order()

    @classmethod
    def random(cls):
        from .vkcommunity import VKCommunity
        return VKCommunity.random(1).objects[0]

    async def data(self, force=False, full=True) -> dict:
        return (await VkMethods.users([self.id], full=full))[0]

    @public_object_method
    async def posts(self) -> VKPosts:
        return VKPosts(await VkMethods.posts(self.id))

    async def name(self):
        return f"{(await self.data(full=False))['first_name']} {(await self.data(full=False))['last_name']}"

    @property
    def url(self):
        return f'https://vk.com/id{self.id}'

    def friends(self):
        from .vkcommunity import VKCommunity
        friend_ids = VkMethods.friends.sync(self.id)
        if isinstance(friend_ids, ParserRealError):
            return VKCommunity()
        friend_ids.append(self.id)
        return VKCommunity(friend_ids, main=self, target='friends')

    async def summary(self):
        result = {
            'valid': self.valid,
            'status': (await self.status()).name,
            'img': 'https://vk.com/images/deactivated_100.png?ava=1',
            'name': 'Пользователь не валиден',
        }
        if not self.valid:
            return result
        data = await self.data()
        return {
            **result,
            'id': self.id,
            'url': self.url,
            'name': await self.name(),
            'img': data.get('photo_200', NO_AVA_IMG),
            'username': data.get("screen_name", 'id' + str(self.id)),
            'verified': data.get('verified', False),
            'private': self.status() == AccountStatus.PRIVATE,
        }


from .vkcommunity import VKCommunity

VKUser._many_media_cls = VKCommunity

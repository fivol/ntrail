import logging
import re
import typing

from core.constants import GroupStatus
from core.module.layers import public_object_method
from core.module.single_entity import SingleEntity
from worker import VkMethods

logger = logging.getLogger()


class VKGroup(SingleEntity):

    def __init__(self, group, **kwargs):
        super().__init__()
        self.id = None
        if isinstance(group, int):
            self.id = group
        elif isinstance(group, dict):
            self.id = group['id']
            self._data = group
        elif group is not None:
            raise TypeError('VKGroup wrong type', type(group))

    @classmethod
    async def create(cls, group):
        if isinstance(group, str):
            username = re.search(r'vk\.com/([a-zA-Z0-9.]+)', group)
            if username:
                username = username.group(1)
            data = await VkMethods.resolve(username)
            group = VKGroup(data)
            return group

        return VKGroup(group)

    async def data(self, force=False):
        return await VkMethods.groups(self.id)

    async def members(self, count=None):
        from core.modules.vk.vkcommunity import VKCommunity
        members = await VkMethods.members(self.id, count=count)
        return VKCommunity(members)

    async def posts(self):
        return await VkMethods.posts(-self.id)

    async def status(self) -> GroupStatus:
        data = await self.data()
        if isinstance(data, Exception):
            return GroupStatus.ABSENT
        if 'deactivated' in data:
            return GroupStatus.DEACTIVATED
        else:
            return GroupStatus.VALID

    async def valid(self):
        return await self.status() == GroupStatus.VALID

    @property
    def url(self):
        # TODO
        raise NotImplementedError

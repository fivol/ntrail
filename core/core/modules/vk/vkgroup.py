import logging
import re
import typing

from core.constants import GroupStatus
from core.helpers.utils import init_with_result
from core.module.single_entity import SingleEntity
from pycommon.decors import cache_method_ignore_args
from worker import VKMethods

logger = logging.getLogger()


class VKGroup(SingleEntity):

    def __init__(self, group, type_=None, **kwargs):
        self.id = None
        self.type = type_
        super().__init__(group, **kwargs)

    @classmethod
    async def create(cls, group):
        if isinstance(group, str):
            username = re.search(r'vk\.com/([a-zA-Z0-9.]+)', group)
            id_ = None
            status = None
            if username:
                username = username.group(1)
            if not username and isinstance(group, str):
                username = group
            group_resolved = await VKMethods.resolve(username)
            if not isinstance(group_resolved, dict):
                logger.info('VKUser username does not exist "{}"', username)
                status = GroupStatus.ABSENT
            elif group_resolved.get('type') in ['page', 'group', 'public']:
                id_ = group_resolved.get('object_id')
            else:
                logger.info('VKGroup username type is "{}"', group_resolved.get('type'))
                status = GroupStatus.ABSENT
            group = VKGroup(id_, type_=group_resolved.get('type'), status=status)
            return group

        return VKGroup(group)

    @cache_method_ignore_args
    @init_with_result
    async def data(self) -> dict:
        return (await VKMethods.groups_ids([self.id]))[0]

    async def members(self, count=None, **kwargs):
        from core.modules.vk.vkcommunity import VKCommunity
        members = await VKMethods.members(self.id, count=count, **kwargs)
        return VKCommunity(members)

    async def posts(self):
        return await VKMethods.posts(-self.id)

    @cache_method_ignore_args
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

    async def name(self):
        data = await self.data()
        return data['name']

    @property
    def url(self):
        # TODO
        raise NotImplementedError

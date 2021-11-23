import asyncio
import logging

from worker.parsers.vk.session import VkApiSession
from worker.credentials.adapter import AdapterBase
from worker.credentials.models import bind
from worker.credentials.db import AccountsAccess, AccessStatus


logger = logging.getLogger(__name__)


class VKAdapter(AdapterBase):
    service = 'vk'

    @classmethod
    async def check(cls, access, key_type):
        try:
            api = VkApiSession(key=access, key_type=key_type).create(access)
            await api.users.get(user_ids=[1], lang='ru')
            return True
        except:
            return False

    @classmethod
    async def create_accesses(cls, max_count=None):
        access = await AccountsAccess.get_access(service=cls.service, status=AccessStatus.unknown, count=max_count, acquire=False)
        for single_access in access:
            if await cls.check(single_access, f'vk.{single_access.type}'):
                await AccountsAccess.set_access_status(single_access, AccessStatus.active)
            else:
                await AccountsAccess.set_access_status(single_access, AccessStatus.denied)


async def main():
    await bind()
    await VKAdapter.create_accesses()

if __name__ == '__main__':
    asyncio.run(main())

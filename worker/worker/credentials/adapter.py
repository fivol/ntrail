import asyncio
import logging

from worker.credentials.db import AccountsAccess, AccessStatus, AccountStatus

from worker.credentials.models import DBAccount

logger = logging.getLogger()


class AdapterBase:
    service = None

    @classmethod
    async def get_access(cls, type_=None, max_count=100):
        access = await AccountsAccess.get_access(count=max_count, type_=type_, service=cls.service,
                                                 status=AccessStatus.active, acquire=True)
        assert len(access) <= max_count
        if len(access) == max_count:
            return access
        await cls.create_accesses(max_count=max_count - len(access))
        remain = await AccountsAccess.get_access(count=max_count - len(access), service=cls.service, type_=type_,
                                                 status=AccessStatus.active, acquire=True)
        return access + remain

    @classmethod
    async def return_access(cls, reason):
        pass

    @classmethod
    async def create_accesses(cls, max_count=None):
        raise NotImplementedError

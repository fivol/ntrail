import logging

from worker.credentials.db import AccountsAccess, AccessStatus, AccountStatus

from worker.credentials.models import DBAccount

logger = logging.getLogger()


class AdapterBase:
    service = None

    @classmethod
    async def get_access(cls, type_=None, max_count=None):
        access = await AccountsAccess.get_access(count=max_count, type_=type_, service=cls.service, status=AccessStatus.active)
        if len(access) == max_count:
            return access
        await cls._create_accesses(max_count=max_count - len(access))
        return await AccountsAccess.get_access(count=max_count, service=cls.service, status=AccessStatus.active)

    @classmethod
    async def return_access(cls, reason):
        pass

    @classmethod
    async def _create_accesses(cls, max_count=None):
        accounts = await AccountsAccess.get_accounts(service=cls.service, count=max_count, status=AccountStatus.unknown)
        if not accounts:
            logger.warning('No free accounts to create access')
            return
        for account in accounts:
            await cls._create_access(account)

    @classmethod
    async def _create_access(cls, account: DBAccount):
        pass

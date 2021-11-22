from worker.credentials.models import *


class ServiceName:
    vk = 'vk'
    ig = 'ig'


class AccessStatus:
    unknown = 'UNKNOWN'
    active = 'ACTIVE'
    access_denied = 'DENIED'
    waiting = 'WAITING'


class AccountStatus:
    unknown = 'UNKNOWN'
    alive = 'ALIVE'
    banned = 'BANNED'
    absent = 'ABSENT'


class AccountsAccess:
    @classmethod
    async def get_access(cls, service: str, status: AccountStatus, type_=None, count=None):
        where = (DBAccount.service == service) & (DBAccess.status == status)
        if type_:
            where = where & (DBAccess.type == type_)
        return await DBAccount.join(DBAccess).select(where).gino.all()

    @classmethod
    async def create_access(cls, account: DBAccount, data: dict, token=None):
        await DBAccess.create(
            account_id=account.id,
            data=data,
            status=AccessStatus.active,
            token=token
        )
        logger.info('Create new access: %s', account)

    @classmethod
    async def get_accounts(cls, service: str, status: AccountStatus, count=1) -> list:
        return await db.all(db.select(DBAccount).
                            where((DBAccount.service == service) & (DBAccount.status == status)).
                            limit(count))

    @classmethod
    async def set_access_status(cls, access: DBAccess, status: AccessStatus):
        await DBAccess.update.values(status=status).where(DBAccess.id == access.id).gino.status()


async def main():
    await bind()


if __name__ == '__main__':
    asyncio.run(main())

from datetime import datetime, timedelta

from sqlalchemy import select

from worker.credentials.access import AccessModel
from worker.credentials.models import *


class ServiceName:
    vk = 'vk'
    ig = 'ig'


class AccessStatus:
    unknown = 'UNKNOWN'
    active = 'ACTIVE'
    denied = 'DENIED'
    waiting = 'WAITING'


class AccountStatus:
    unknown = 'UNKNOWN'
    alive = 'ALIVE'
    banned = 'BANNED'
    absent = 'ABSENT'


class AccountsAccess:
    @classmethod
    async def get_access(cls, service: str, status: AccountStatus, type_=None, count=None, acquire=False):
        async with db.transaction() as tx:
            where = (DBAccount.service == service) & (DBAccess.status == status)
            is_free = (DBAccess.free.is_(True)) | (
                    DBAccess.last_acquire + timedelta(minutes=30) < datetime.now())
            where = where & is_free
            if type_:
                where = where & (DBAccess.type == type_)
            query = select([DBAccess.id, DBAccess.type, DBAccess.data, DBAccess.token, DBAccount.service]).select_from(
                DBAccess.join(DBAccount)).where(where)
            if count:
                query = query.limit(count)
            models = await query.gino.all()
            if acquire:
                await DBAccess.update.values(last_acquire=datetime.now(), free=False).where(
                    DBAccess.id.in_([item.id for item in models])).gino.status()
            return models

    @classmethod
    async def return_access(cls, models: list[DBAccess]):
        await DBAccess.update.values(free=True).where(
            DBAccess.id.in_([item.id for item in models])).gino.status()

    @classmethod
    async def update_access(cls, models: list[DBAccess]):
        await DBAccess.update.values(last_acquire=datetime.now(), free=False).where(
            DBAccess.id.in_([item.id for item in models])).gino.status()

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
        await DBAccess.update.values(status=status, free=True).where(DBAccess.id == access.id).gino.status()


async def main():
    await bind()


if __name__ == '__main__':
    asyncio.run(main())

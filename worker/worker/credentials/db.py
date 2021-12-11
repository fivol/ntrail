from datetime import datetime, timedelta
from sqlalchemy import select, update

from worker.credentials.models import *


class ServiceName:
    vk = 'vk'
    ig = 'ig'


class AccessStatus:
    unknown = 'UNKNOWN'
    active = 'ACTIVE'
    waiting = 'WAITING'
    suspicious_activity = 'SUSPICIOUS'
    auth_error = 'AUTH'
    login_redirect = 'LOGIN'
    # Some unknown error happened
    unknown_error = 'ERROR'


class AccountStatus:
    unknown = 'UNKNOWN'
    alive = 'ALIVE'
    banned = 'BANNED'
    # Словил подозрительную активность
    suspicious = 'SUSPICIOUS'
    # Выкинуло на логин
    login = 'LOGIN'
    absent = 'ABSENT'


class AccountsAccess:
    @classmethod
    async def get_access(cls, service: str, status: AccountStatus, type_=None, count=None, acquire=False,
                         ids: list = None):
        async with db.acquire() as conn:
            async with conn.transaction() as tx:
                where = (DBAccount.service == service) & (DBAccess.status == status)
                is_free = DBAccess.free == True
                where = where & is_free
                if type_:
                    where = where & (DBAccess.type == type_)
                if ids:
                    where = (DBAccess.id.in_(ids))

                query = select([DBAccess.id]).select_from(
                    DBAccess.join(DBAccount)).where(where).order_by(db.text('random()'))

                if count:
                    query = query.limit(count)

                if acquire:
                    result = await update(DBAccess).values(last_acquire=datetime.now(), free=False). \
                        where(DBAccess.id.in_(query)). \
                        returning(
                        db.text('*')).gino.all()
                    return result
                else:
                    return await select(DBAccess).where(DBAccess.id.in_(query)).gino.all()

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
        logger.info('CREATE ACCESS: %s', token)
        async with db.transaction() as tx:
            await DBAccess.create(
                account_id=account.id,
                data=data,
                status=AccessStatus.active,
                token=token
            )
            logger.info('Create new access: %s', account)
            await DBAccount.update.values(status=AccountStatus.alive).where(DBAccount.id == account.id).gino.status()

    @classmethod
    async def get_not_banned_accounts_without_access(cls, service: str, count=1) -> list:
        return await db.all(db.select(DBAccount).select_from(DBAccount.outerjoin(DBAccess)).
                            where(
            (DBAccount.service == service) & (DBAccount.status != AccountStatus.banned) & (
                DBAccess.account_id.is_(None))).
                            limit(count))

    @classmethod
    async def set_access_status(cls, access: DBAccess, status: AccessStatus):
        await DBAccess.update.values(status=status, free=True).where(DBAccess.id == access.id).gino.status()


async def main():
    await bind()


if __name__ == '__main__':
    asyncio.run(main())

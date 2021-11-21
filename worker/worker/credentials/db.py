from worker.credentials.models import *


class ServiceName:
    vk = 'vk'
    ig = 'ig'


class AccessStatus:
    unknown = 'UNKNOWN'
    active = 'ACTIVE'
    access_denied = 'DENIED'


class AccountsAccess:
    @classmethod
    async def get_access(cls, service: str, type_=None, count=None):
        return await DBAccount.join(DBAccess).select(DBAccount.service == service).gino.all()

    @classmethod
    async def get_accounts(cls, service: str, count=1):
        return await db.all(db.select(DBAccount).where(DBAccount.service == service).limit(count))


async def main():
    await bind()
    print(await AccountsAccess.get_accounts('ig'))


if __name__ == '__main__':
    asyncio.run(main())

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
    def get_access(cls, service: str, type_=None, count=None):
        pass


async def main():
    await bind()
    print(await DBAccount.join(DBAccess).select(DBAccount.service == 'vk').gino.all())


if __name__ == '__main__':
    asyncio.run(main())

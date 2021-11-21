import asyncio
from worker.credentials.models import bind, DBAccount, DBAccess
from worker.credentials.db import AccountsAccess
from igramscraper.instagram import Instagram


class IGAdapter:
    async def check(self, ):
        pass


async def main():
    await bind()
    account = (await AccountsAccess.get_accounts(service='ig'))[0]
    ig = Instagram()
    ig.cookie = account['data']['cookie']
    print(ig.get_account('fiobond'))


if __name__ == '__main__':
    asyncio.run(main())

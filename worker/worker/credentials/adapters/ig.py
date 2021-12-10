from asyncpg.exceptions import UniqueViolationError

from worker.credentials.adapter import AdapterBase
from worker.credentials.db import *
from worker.parsers.ig.instagramscraper.instagram import Instagram, InstagramAuthException


logger = logging.getLogger(__name__)


class IGAdapter(AdapterBase):
    service = 'ig'

    @classmethod
    async def _create_access(cls, account: DBAccount):
        try:
            ig = Instagram()
            data = account.data
            await ig.auth(username=account.login, password=account.password, cookie=data.get('cookie'))
            await AccountsAccess.create_access(account, {'cookie': ig.cookie}, token=ig.cookie.get('sessionid'))
        except InstagramAuthException:
            logger.exception('Failed to create access')
        except UniqueViolationError:
            logger.debug('Access already exist')

    @classmethod
    async def create_accesses(cls, max_count=1):
        accounts = await AccountsAccess.get_not_banned_accounts_without_access(service=cls.service, count=max_count)
        if not accounts:
            logger.warning('No free accounts to create access')
            return
        await asyncio.gather(*[cls._create_access(account) for account in accounts], return_exceptions=True)


# ME 12638820603
async def main():
    await bind()
    print(await IGAdapter.get_access(max_count=2))


if __name__ == '__main__':
    asyncio.run(main())

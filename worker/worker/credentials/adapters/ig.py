import asyncio
import logging
from pprint import pprint
from asyncpg.exceptions import UniqueViolationError

from worker.credentials.adapter import AdapterBase
from worker.credentials.models import bind, DBAccount, DBAccess
from worker.credentials.db import *
from igramscraper.instagram import Instagram, InstagramAuthException


logger = logging.getLogger(__name__)


class IGAdapter(AdapterBase):
    service = 'ig'

    @classmethod
    async def _create_access(cls, account: DBAccount):
        try:
            ig = Instagram()
            data = account.data
            await ig.auth(username=account.login, password=account.password, cookie=data.get('cookie'))
            await AccountsAccess.create_access(account, ig.cookie, token=ig.cookie.get('sessionid'))
        except InstagramAuthException:
            logger.exception('Failed to create access')
        except UniqueViolationError:
            logger.debug('Access already exist')


# ME 12638820603
async def main():
    await bind()
    print(await IGAdapter.get_access(2))
    # print(ig.get_following(3))


if __name__ == '__main__':
    asyncio.run(main())

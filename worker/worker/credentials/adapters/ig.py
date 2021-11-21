import asyncio
import logging

from worker.credentials.models import bind, DBAccount, DBAccess
from worker.credentials.db import AccountsAccess
from igramscraper.instagram import Instagram, LoginRedirectError


logger = logging.getLogger(__name__)


# ME 12638820603
async def main():
    await bind()
    account = (await AccountsAccess.get_accounts(service='ig'))[0]
    # ig = Instagram()
    # ig.user_session = account['data']['cookie']
    headers = await IGAdapter.connect('abc', 'sdff', cookie=None)
    await AccountsAccess.create_access(account, headers)

    # print(ig.get_following(3))


if __name__ == '__main__':
    asyncio.run(main())

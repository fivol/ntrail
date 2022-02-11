import asyncio
import logging
from pprint import pprint

from worker import Engine, IGMethods, VKMethods
from worker.credentials.credentials import Credentials
from worker.parsers.ig.instagramscraper.instagram import Instagram
from worker.parsers.ig.session import IgApiSession
from worker.selenium.selenium_request import SeleniumRequest

logger = logging.getLogger(__name__)


# async def open_instagram_selenium(id):
#     access = await Credentials.get_access('ig', 1, ids=[id])
#     session = IgApiSession(access[0], 'ig')
#     SeleniumRequest().block_get('https://instagram.com/', session.session.cookie)


async def main():
    async with Engine(caching=False):
        # 5749832861
        # me 12638820603
        # nikita 8368846410
        # pprint(await VKMethods.posts(-172053584, count=1))
        # pprint(await VKMethods.poll(owner_id=-172053584, poll_id=669155401))
        print(await VKMethods.users([245089915]))

if __name__ == '__main__':
    asyncio.run(main())

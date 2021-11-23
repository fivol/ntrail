import asyncio
import logging
from pprint import pprint

from worker import Engine, IgMethods, VkMethods

logger = logging.getLogger(__name__)


async def main():
    async with Engine(caching=False):
        # 5749832861
        # me 12638820603
        # nikita 8368846410
        # print(await IgMethods.resolve('nikitagabow'))
        followers = await IgMethods.following(8368846410, all_=True)
        pprint(followers)

if __name__ == '__main__':
    asyncio.run(main())

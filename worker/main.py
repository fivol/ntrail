import asyncio
import logging
from pprint import pprint

from worker import Engine, IgMethods

logger = logging.getLogger(__name__)


async def main():
    async with Engine():
        # 5749832861
        # me 12638820603
        data = await IgMethods.following(12638820603)
        await asyncio.sleep(2)
        data = await IgMethods.following(12638820603)
        print(len(data))

if __name__ == '__main__':
    asyncio.run(main())

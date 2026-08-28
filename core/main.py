import asyncio
import warnings
from pprint import pprint

import core.config # noqa
from core import IGUser, VKUser, VKPoll
from worker import Engine

warnings.simplefilter('ignore')


async def main():
    async with Engine(caching=True):
        user = await VKUser.create('ffboris')
        data = await user.data()
        pprint(data)

if __name__ == '__main__':
    asyncio.run(main())

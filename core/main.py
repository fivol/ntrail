import asyncio
import warnings
from pprint import pprint

import core.config # noqa
from core import IGUser, VKUser
from worker import Engine

warnings.simplefilter('ignore')


async def main():
    async with Engine(caching=True):
        user = await IGUser.create('fiobond')
        wall = await user.wall()
        print(await wall[0].likes())

if __name__ == '__main__':
    asyncio.run(main())

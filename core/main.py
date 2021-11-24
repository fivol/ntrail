import asyncio
import warnings
import core.config # noqa
from core import IGUser, VKUser
from worker import Engine

warnings.simplefilter('ignore')


async def main():
    async with Engine(caching=False):
        user = await IGUser.create('fiobond')
        print(user.id)


if __name__ == '__main__':
    asyncio.run(main())

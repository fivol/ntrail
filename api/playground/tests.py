import asyncio
import logging

from core import VKUser
from server.plugin.register import register_plugins
from worker import Engine

register_plugins()

logger = logging.getLogger()


async def main():
    user = await VKUser.create('ffboris')
    groups = await user.groups()
    print(await groups.data())

if __name__ == '__main__':
    with Engine(caching=False):
        asyncio.get_event_loop().run_until_complete(main())

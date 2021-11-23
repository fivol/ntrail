import asyncio
import logging

from worker import Engine, VkMethods

logger = logging.getLogger(__name__)


async def main():
    async with Engine():
        users = await VkMethods.friends((await VkMethods.resolve('aido4kas'))['object_id'])
        print(await VkMethods.friends.map(users))

if __name__ == '__main__':
    asyncio.run(main())

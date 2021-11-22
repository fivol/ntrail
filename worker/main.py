import asyncio
import logging

from worker import Engine, VkMethods

logger = logging.getLogger(__name__)


async def main():
    async with Engine():
        await VkMethods.resolve('ffboris')

if __name__ == '__main__':
    asyncio.run(main())

"""
400 queries with caching: 2140 rps
1000: 290
100 new queries (cache misses) - 200 rps (20 tokens) 2500 with cache
1000 users.get queries without caching - 313 rps (20 tokens) with normal limits (3 and 5 rps per token)

10000 users data collected with rps 3797 
25000 with rps 4459. Splitter divided it into 25 users.get queries and execute completes with single query
-> 25000 users in one query
"""

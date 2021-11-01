import asyncio
import time
import config  # noqa
from timeit import default_timer as timer

from worker import Engine, VkMethods


async def calculate_rps(epochs=10, count=100):
    rps_measures = []
    for ep in range(epochs):
        ids = set([i for i in range(count, 2*count)])
        assert len(ids) == count
        start = timer()
        users = await asyncio.gather(
            *[
                VkMethods.users([i])
                for i in ids
            ]
        )
        users_ids = {user[0]['id'] for user in users}
        assert ids == users_ids
        elapsed = timer() - start
        rps = count / elapsed
        rps_measures.append(rps)
        print(f'Epoch {ep}, rps: {rps}')

    mean_rps = sum(rps_measures) / epochs
    print('Mean rps:', mean_rps)
    return mean_rps


async def main():
    # begin = timer()
    # count = 25000
    # users = await asyncio.gather(*[VkMethods.users([i]) for i in range(1, 10)])
    # print(len(users))
    # print(users)
    # print(int(count / (timer() - begin)))
    # print(await calculate_rps(epochs=10, count=10))
    # groups = await VkMethods.groups(91050183)
    print((await VkMethods.members(172053584, count=10000)).__len__())


if __name__ == '__main__':
    with Engine(caching=False):
        asyncio.get_event_loop().run_until_complete(main())


"""
400 queries with caching: 2140 rps
1000: 290
100 new queries (cache misses) - 200 rps (20 tokens) 2500 with cache
1000 users.get queries without caching - 313 rps (20 tokens) with normal limits (3 and 5 rps per token)

10000 users data collected with rps 3797 
25000 with rps 4459. Splitter divided it into 25 users.get queries and execute completes with single query
-> 25000 users in one query
"""

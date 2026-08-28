import asyncio
from pprint import pprint

from core import VKUser
from server.plugin.register import register_plugins
from worker import Engine

# http://nlpx.net/archives/57
register_plugins()


async def main():
    user = await VKUser.create('https://vk.com/ffboris')
    groups = await user.groups()
    data = await groups.data()
    names = [group['name'] for group in data]
    pprint(IDFCalculator.calculate(names))
    return
    # print(await groups[4].members())
    # return
    pools = await groups.pools()
    for pool in pools:
        # print(pool)
        # print(pool.size)
        names = [await group.name() for group in pool.objects()]
        features = IDFCalculator.calculate(names)[:5]
        if features:
            print(features[:3])
    # print(graph.nodes)
    # data = await groups.data()
    # names = [user.get('name') for user in data]

    # response = await PluginManager({'user': 'aido4kas'}, input_plugins=['user'], options=['user-interests.groups']).execute()
    # pprint(response)

if __name__ == '__main__':
    with Engine(caching=True):
        asyncio.get_event_loop().run_until_complete(main())

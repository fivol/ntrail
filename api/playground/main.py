import asyncio
from pprint import pprint

from core import VKUser, VKCommunity
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from worker import Engine
from worker import VkMethods

register_plugins()


async def main():
    arguments = {'user': 'https://vk.com/aido4kas'}
    # print(sum([VKCommunity() for post in range(33)], start=VKCommunity()))
    response = await PluginManager(arguments, input_plugins=['user'], options=['user-fans']).execute()
    pprint(response)

if __name__ == '__main__':
    with Engine(caching=False):
        asyncio.get_event_loop().run_until_complete(main())

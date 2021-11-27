import asyncio
import logging
from pprint import pprint

from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from worker import Engine

register_plugins()

logger = logging.getLogger()


async def main():
    res = await PluginManager({'user': 'https://vk.com/aido4kas'}, input_plugins=['user'], options=['user-fans']).execute()
    pprint(res)

if __name__ == '__main__':
    with Engine(caching=True):
        asyncio.get_event_loop().run_until_complete(main())

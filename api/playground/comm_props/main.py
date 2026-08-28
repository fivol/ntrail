import asyncio
import logging
from pprint import pprint

from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from worker import Engine

register_plugins()

logger = logging.getLogger()


async def main():
    # https://vk.com/bigdantheone
    res = await PluginManager({'user': 'https://vk.com/bigdantheone'}, input_plugins=['user', 'friends'], options=['user.data']).execute()
    pprint(res)

if __name__ == '__main__':
    with Engine(caching=False):
        asyncio.get_event_loop().run_until_complete(main())

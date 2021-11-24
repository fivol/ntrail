import asyncio
import logging
from collections import Counter
from contextlib import suppress
from datetime import datetime
from pprint import pprint

from tqdm import tqdm, trange

from core import VKUser, VKCommunity
from core.modules.vk.vkgroups import VKGroups
from core import IGUser
from server.helpers.tied_value import TiedValue
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.user import UserDescribePlugin
from worker import Engine
from worker.instagramscraper.exception.instagram_not_found_exception import InstagramNotFoundException

register_plugins()

logger = logging.getLogger(__name__)


async def main():
    async with Engine(caching=False):
        response = await PluginManager({'user': 'https://vk.com/katya11111'}, input_plugins=['user'],
                                       options=['find-instagram']).execute()
        pprint(response)


if __name__ == '__main__':
    asyncio.run(main())


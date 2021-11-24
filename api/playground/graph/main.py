import asyncio
import logging
from contextlib import suppress
from datetime import datetime
from pprint import pprint

from tqdm import tqdm, trange

from core import VKUser, VKCommunity
from core.modules.vk.vkgroups import VKGroups
from server.helpers.tied_value import TiedValue
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.register_date import UserRegistrationDate
from server.routes.vk.plugins.representer import UsersRepresentation
from worker import Engine
from worker import VKMethods

register_plugins()

logger = logging.getLogger()


async def main():
    res = await PluginManager({'user': 'https://vk.com/aido4kas'}, input_plugins=['user'], options=['user-fans']).execute()
    pprint(res)

if __name__ == '__main__':
    with Engine(caching=True):
        asyncio.get_event_loop().run_until_complete(main())

import asyncio
import json
import logging
from contextlib import suppress
from datetime import datetime
from pprint import pprint

from tqdm import tqdm, trange

from core import VKUser, VKCommunity
from core.modules.vk.vkgroups import VKGroups
from server.helpers.content_utils import make_json_serializable
from server.helpers.tied_value import TiedValue
from server.helpers.utils import absolute_path
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.register_date import UserRegistrationDate
from worker import Engine
from worker import VkMethods

register_plugins()

logger = logging.getLogger()


async def main():
    res = await PluginManager({'user': 'ffboris'}, input_plugins=['user', 'friends'], options=['user-friends']).execute()
    with open(absolute_path(__file__, '.data.json'), 'w') as f:
        f.write(json.dumps(make_json_serializable(res), indent=4))
    pprint(res)

if __name__ == '__main__':
    with Engine(caching=False):
        asyncio.get_event_loop().run_until_complete(main())

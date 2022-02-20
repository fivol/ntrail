import asyncio
import logging
import os
from collections import Counter
from contextlib import suppress
from datetime import datetime
from pprint import pprint
from time import sleep

from selenium.common.exceptions import NoSuchWindowException
from tqdm import tqdm, trange

from core import VKUser, VKCommunity
from core.modules.vk.vkgroups import VKGroups
from core import IGUser, VKGroup
from server.helpers.tied_value import TiedValue
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.user import UserDescribePlugin
from worker import Engine, IGMethods

register_plugins()


async def main():
    async with Engine():
        user = VKUser(245089915)
        print(await user.friends())

if __name__ == '__main__':
    asyncio.run(main())

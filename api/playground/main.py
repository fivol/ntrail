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
from core import IGUser
from server.helpers.tied_value import TiedValue
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.user import UserDescribePlugin
from worker import Engine, IGMethods

register_plugins()

logger = logging.getLogger(__name__)


async def main():
    async with Engine():
        # 'QVFBbEtiVEUtalRuMm9SWFJadU1nTDI4eEdZcTljUUdaTHRHUTRpbmt5ZHVuR0FJNWVBNjFfRFY3TWhGc1IySmh4ZFo5TGQ0ckFFeWE0QjdybjROV0xFdg=='
        # 4367352634
        print(await IGUser(4367352634).followers(count=20))
        # await IGMethods.followers(4367352634, count=10, end_cursor='QVFBbEtiVEUtalRuMm9SWFJadU1nTDI4eEdZcTljUUdaTHRHUTRpbmt5ZHVuR0FJNWVBNjFfRFY3TWhGc1IySmh4ZFo5TGQ0ckFFeWE0QjdybjROV0xFdg==')


if __name__ == '__main__':
    asyncio.run(main())

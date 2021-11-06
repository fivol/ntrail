import asyncio
import concurrent
import logging
import re
from collections import Counter
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import suppress
from datetime import datetime
from pprint import pprint
from time import time

from pymystem3 import Mystem
from tqdm import tqdm, trange

from core import VKUser, VKCommunity
from core.modules.vk.vkgroups import VKGroups
from server.helpers.tied_value import TiedValue
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.register_date import UserRegistrationDate
from worker import Engine
from worker import VkMethods
import nltk
import pymorphy2

# http://nlpx.net/archives/57
register_plugins()

logger = logging.getLogger()


async def main():
    pass


if __name__ == '__main__':
    with Engine(caching=False):
        asyncio.get_event_loop().run_until_complete(main())

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
from server.routes.vk.plugins.tf_idf import IDFCalculator
from worker import Engine
from worker import VkMethods
import nltk
import pymorphy2

# http://nlpx.net/archives/57
register_plugins()

logger = logging.getLogger()


async def main():
    user = await VKUser.create('https://vk.com/ffboris')
    groups = await user.groups()
    data = await groups.data()
    names = [group['name'] for group in data]
    IDFCalculator.calculate(names)
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

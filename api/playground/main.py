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
from worker import Engine
from worker.instagramscraper.exception.instagram_not_found_exception import InstagramNotFoundException

register_plugins()

logger = logging.getLogger(__name__)


async def main():
    print('hello')
    pass
    # async with Engine(caching=False):
    #     response = await PluginManager({'user': 'ffboris'}, input_plugins=['user'],
    #                                    options=['find-instagram']).execute()
    #     pprint(response)


from selenium import webdriver

driver = webdriver.Firefox(executable_path='/Users/fiobond/Downloads/geckodriver')
data ={"cookie": {"mid": "YZ5HkwABAAHNnv_mktPsD868WvIC", "rur": "RVA,50511106389,1669298963:01f7c09254a5802a3b98ee2f757244427196bbad28375e066dbaacc3874ff86e564136a6", "igfl": "", "ds_user": "", "csrftoken": "eppqDEs4cJEA2S1yZdwiI9scCYP6qRGI", "sessionid": "50511106389%3A25S9tjDnVfjiiY%3A25", "ds_user_id": "50511106389", "authorization": "Bearer IGT:2:eyJkc191c2VyX2lkIjoiNTA1MTExMDYzODkiLCJzZXNzaW9uaWQiOiI1MDUxMTEwNjM4OSUzQTI1Uzl0akRuVmZqaWlZJTNBMjUiLCJzaG91bGRfdXNlX2hlYWRlcl9vdmVyX2Nvb2tpZXMiOnRydWV9", "is_starred_enabled": ""}}

# print(driver.)
# driver.get("https://instagram.com")
# for key, value in data['cookie'].items():
#     driver.add_cookie({'name': key, 'value': value, 'domain': 'instagram.com'})
#
# driver.get("https://instagram.com")
if __name__ == '__main__':
    while True:
        driver.get('https://google.com')
        while True:
            try:
                sleep(1)
                print('title', driver.title)
            except NoSuchWindowException:
                break
        driver.execute_script("window.open('')")


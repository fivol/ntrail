import json
from glbal import logger
from tied_value import TiedValue
from tools import *
from vkuser import VKUser
from vkcommunity import VKCommunity
from vkgroup import VKGroups
from vkuser import VKUser
from vkgroup import VKGroup
from pprint import pprint
from glbal import logger
from igcommunity import IGCommunity
from iguser import IGUser
from models import *
import warnings

# print(VKUser("https://vk.com/id269339915").friends().short_data)
# print(VKUser("https://vk.com/id269339915").friends().process_data())
from selective_query_execute import execute_query, get_query_tokens, TokensGenerator, collect_query_data

warnings.filterwarnings("ignore")

q = 'vkuser id123241667 friends'
# print(VKUser.me().friends().process_data())
# execute_query(q)
# VKUser.generate_random().friends().represent()
# print(collect_query_data('GET vk.user boris2000n'))
# print(collect_query_data('GET vk.users (boris2000n)'))
# print(collect_query_data('GET vk.user boris2000n'))
print(collect_query_data('GET vk.user boris2000n'))

# from vkapi import VKAPI
# print(VKAPI.get_apps_data([2274003]))
#
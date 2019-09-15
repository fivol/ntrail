import warnings
warnings.filterwarnings("ignore")
from baseapi import bapi, BaseAPI
from community_pool import Community
from vkuser import VKUser
from groups_pool import GroupsPool
import pprint
from time import time

user = VKUser('boris2000n')
user.groups.color_graph(algorithm='louvain')


# user = VKUser('boris2000n')
# user.groups.color_graph(algorithm='label_propagation')
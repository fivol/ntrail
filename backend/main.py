import json
from baseapi import bapi, BaseAPI
from vkcommunity import VKCommunity
from vkgroups import VKGroups
from vkuser import VKUser
from vkgroup import VKGroup
from pprint import pprint
from glbal import logger
from instcommunity import InstCommunity
from instuser import InstUser

def make_json_serializable(obj):
    try:
        json.dumps(obj)
        return obj
    except:
        if isinstance(obj, dict):
            return dict([(key, make_json_serializable(value)) for key, value, in obj.items()])
        if isinstance(obj, list):
            return [make_json_serializable(item) for item in obj]

        return str(obj)

# VKUser('boris2000n').friends.pools()
# user = VKUser('boris2000n')
# user.groups.color_graph(algorithm='louvain')


# user = VKUser('boris2000n')
# user.groups.color_graph(algorithm='label_propagation')





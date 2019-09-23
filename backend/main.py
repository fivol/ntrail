import json
from baseapi import bapi, BaseAPI
from community_pool import Community
from groups_pool import GroupsPool
from vkuser import VKUser
from vkgroup import VKGroup


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


bapi.load_memory()
# user = VKUser('boris2000n')
# user.groups.color_graph(algorithm='louvain')


# user = VKUser('boris2000n')
# user.groups.color_graph(algorithm='label_propagation')





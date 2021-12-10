from core import VKUser, VKCommunity
from server.plugin.plugin import BasePlugin


class VKFriendsLonersPlugin(BasePlugin):
    name = 'friends-loners'
    namespace = 'vk'

    def __init__(self, user: VKUser, **kwargs):
        super(VKFriendsLonersPlugin, self).__init__(**kwargs)
        self._user = user

    async def response(self) -> dict:
        friends = await self._user.friends()
        pools = await friends.pools()
        union_pool = sum(pools, VKCommunity())
        single_cluster_nodes = set()
        for node in friends.nodes:
            if node not in union_pool:
                single_cluster_nodes.add(node)
        return {
            'count': len(single_cluster_nodes),
            'percent': round(len(single_cluster_nodes) / len(friends), 2)
        }

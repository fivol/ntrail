from server.plugin import BasePlugin
from core import VKCommunity


class VKFriendsPlugin(BasePlugin):
    name = 'friends'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._friends = None

    def init(self):
        self._friends = self.get_plugin_result('user').friends()

    def get(self) -> VKCommunity:
        return self._friends

    def response(self) -> dict:
        return self.get().data()

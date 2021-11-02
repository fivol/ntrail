from core import VKUser
from server.plugin import BasePlugin


class VKUserPlugin(BasePlugin):
    name = 'user'

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)

        self._user_input = user
        self._user = None

    def init(self):
        self._user = VKUser(self._user_input)

    def result(self):
        return self._user

    def response(self) -> dict:
        return self.result().summary()


class VKUserDataPlugin(BasePlugin):
    name = 'user-data'

    def response(self) -> dict:
        return self.get_plugin_result('user').data()

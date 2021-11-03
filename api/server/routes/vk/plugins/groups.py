from server.plugin.plugin import BasePlugin


class VKGroupsPlugin(BasePlugin):
    name = 'groups'

    def result(self):
        user = self.get_plugin_result('user')
        return user.groups()

    def response(self) -> dict:
        return self.result().summary()

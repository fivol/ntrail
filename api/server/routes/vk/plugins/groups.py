from server.plugin import BasePlugin


class VKGroupsPlugin(BasePlugin):
    name = 'groups'

    def response(self) -> dict:
        return {}

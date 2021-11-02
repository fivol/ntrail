from server.plugin import BasePlugin


class VKBasicPlugin(BasePlugin):
    name = 'basic'

    def response(self) -> dict:
        return {}

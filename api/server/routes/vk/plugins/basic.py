from server.plugin import BasePlugin


class VKBasicPlugin(BasePlugin):
    name = 'basic'

    def response(self) -> dict:
        return self.get_plugin_response('user')

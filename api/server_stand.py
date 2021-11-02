from server.plugin_manager import PluginManager
from server.routes.vk.plugins.user import *
from server.routes.vk.plugins.basic import *
from server.routes.vk.plugins.friends import *
from server.routes.vk.plugins.groups import *
from server.types import ResponseVerbose


class ServerStand:
    _all_plugins = [VKGroupsPlugin, VKUserPlugin, VKFriendsPlugin, VKBasicPlugin, VKUserDataPlugin]

    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, options, verbose=ResponseVerbose.normal, **kwargs):
        assert isinstance(options, list)
        return PluginManager(plugins=self._all_plugins, kwargs=kwargs,
                             verbose=verbose, options=options).execute()

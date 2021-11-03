from server.plugin.plugin_manager import PluginManager

from server.routes.vk.plugins.user import *
from server.routes.vk.plugins.community import *
from server.routes.vk.plugins.connections import *
from server.routes.vk.plugins.groups import *
from worker import assert_imported_once

_plugins = [VKGroupsPlugin, VKUserInput, VKFriendsPlugin, VKBasicPlugin, VKUserDataPlugin]

assert_imported_once()


def register_plugins(plugins):
    for plugin in plugins:
        PluginManager.register_plugin(plugin)


register_plugins(_plugins)

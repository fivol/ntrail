from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.friends import VKUserFriendsPlugin
from server.routes.vk.plugins.instagram import VKFindInstagramPlugin
from server.routes.vk.plugins.interests import VKUserInterestsPlugin
from server.routes.vk.plugins.relatives import VKRelativesPlugin
from server.routes.vk.plugins.special_friends import VKSpecialFriendsPlugin

from server.routes.vk.plugins.user import *
from server.routes.vk.plugins.community import *
from server.routes.vk.plugins.connections import *
from server.routes.vk.plugins.zodiac import *
from server.routes.vk.plugins.loners import *
from server.routes.vk.plugins.fans import *
from server.routes.vk.plugins.groups import *
from worker.helpers.tools import assert_imported_once

_plugins = {VKGroupsPlugin, VKUserInput, VKGroupsInput, VKSpecialFriendsPlugin, VKRelativesPlugin,
            VKFriendsInput, VKUserInterestsPlugin, VKFriendsLonersPlugin, VKUserFriendsPlugin,
            VKUserPlugin, VKCommunityPlugin, VKUserZodiacPlugin, VKUserFansPlugin, UserDescribePlugin, VKFindInstagramPlugin}

assert_imported_once()


def register_plugins():
    for plugin in _plugins:
        PluginManager.register_plugin(plugin)


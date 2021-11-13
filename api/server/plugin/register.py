from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.friends import UserFriendsPlugin
from server.routes.vk.plugins.interests import UserInterestsPlugin
from server.routes.vk.plugins.special_friends import SpecialFriendsPlugin

from server.routes.vk.plugins.user import *
from server.routes.vk.plugins.community import *
from server.routes.vk.plugins.connections import *
from server.routes.vk.plugins.zodiac import *
from server.routes.vk.plugins.loners import *
from server.routes.vk.plugins.fans import *
from server.routes.vk.plugins.groups import *
from worker import assert_imported_once

_plugins = [VKGroupsPlugin, VKUserInput, VKGroupsInput, SpecialFriendsPlugin,
            VKFriendsInput, UserInterestsPlugin, VkFriendsLonersPlugin, UserFriendsPlugin,
            VKUserData, VKCommunityPlugin, UserZodiacPlugin, UserFansPlugin]

assert_imported_once()


def register_plugins():
    for plugin in _plugins:
        PluginManager.register_plugin(plugin)


from server.plugin.plugin_manager import PluginManager
from server.routes.vk.plugins.friends import UserFriendsPlugin
from server.routes.vk.plugins.instagram import FindInstagramPlugin
from server.routes.vk.plugins.interests import UserInterestsPlugin
from server.routes.vk.plugins.relatives import RelativesPlugin
from server.routes.vk.plugins.special_friends import SpecialFriendsPlugin

from server.routes.vk.plugins.user import *
from server.routes.vk.plugins.community import *
from server.routes.vk.plugins.connections import *
from server.routes.vk.plugins.zodiac import *
from server.routes.vk.plugins.loners import *
from server.routes.vk.plugins.fans import *
from server.routes.vk.plugins.groups import *
from worker.helpers.tools import assert_imported_once

_plugins = {VKGroupsPlugin, VKUserInput, VKGroupsInput, SpecialFriendsPlugin, RelativesPlugin,
            VKFriendsInput, UserInterestsPlugin, VkFriendsLonersPlugin, UserFriendsPlugin,
            VKUserPlugin, VKCommunityPlugin, UserZodiacPlugin, UserFansPlugin, UserDescribePlugin, FindInstagramPlugin}

assert_imported_once()


def register_plugins():
    for plugin in _plugins:
        PluginManager.register_plugin(plugin)


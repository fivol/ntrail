from pprint import pprint

from core import VKUser
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from worker import Engine
from worker import VkMethods

register_plugins()

if __name__ == '__main__':
    with Engine(caching=False):
        print(VKUser('https://vk.com/id151973251').posts()[1].likes().nodes)
        # arguments = {'user': 'https://vk.com/ffboris'}
        # response = PluginManager(arguments, input_plugins=['user'], options=['user', 'user.data']).execute()
        # pprint(response)

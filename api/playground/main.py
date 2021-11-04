from pprint import pprint

from core import VKUser, VKCommunity
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from worker import Engine
from worker import VkMethods

register_plugins()

if __name__ == '__main__':
    with Engine(caching=False):
        # print(VkMethods.resolve.sync('mfisdajfo'))
        # print(VKUser('https://vk.com/id151973251').posts()[1].likes().nodes)
        arguments = {'user': 'https://vk.com/aido4kas'}
        # print(sum([VKCommunity() for post in range(33)], start=VKCommunity()))
        response = PluginManager(arguments, input_plugins=['user'], options=['user-fans']).execute()
        pprint(response)
        # print((VKCommunity([1, 2, 2, 4, 2]) + VKCommunity([1])).counter())

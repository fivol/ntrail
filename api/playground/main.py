from pprint import pprint

from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from worker import Engine

register_plugins()

if __name__ == '__main__':
    with Engine(caching=False):
        arguments = {'user': 'ffboris'}
        response = PluginManager(arguments, input_plugins=['user', 'friends'], options=['community.size']).execute()
        pprint(response)

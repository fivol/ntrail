import typing
from abc import ABCMeta, abstractmethod


class BasePlugin(metaclass=ABCMeta):
    name: str

    def __init__(self, manager=None, verbose=None, **kwargs):
        self.__manager = manager
        self._verbose = verbose

    def result(self) -> typing.Any:
        """Main method of plugin, should return result (some object or dict)"""
        return self.response()

    @abstractmethod
    def response(self) -> dict:
        """Return json dict to response, that will be shown to user"""
        pass

    def init(self):
        """Called after constructor"""
        pass

    def get_plugin(self, name):
        return self.__manager.get_plugin(name)

    def get_plugin_result(self, name):
        return self.__manager.get_plugin_result(name)

    def get_plugin_response(self, name):
        return self.__manager.get_plugin_response(name)

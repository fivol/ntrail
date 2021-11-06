from __future__ import annotations
import typing
from abc import ABCMeta, abstractmethod

from server.types import ResponseVerbose


class Plugin:
    name: str


class BasePlugin(Plugin):
    broken = False

    def __init__(self, manager=None, verbose: ResponseVerbose = None, **kwargs):
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

    def get_plugin(self, name) -> BasePlugin:
        return self.__manager.get_plugin(name)


class InputPlugin(Plugin):

    @classmethod
    @abstractmethod
    def read(cls, **kwargs) -> dict:
        pass


import typing

from fastapi import HTTPException, status

from server.plugin import BasePlugin
from server.types import ResponseVerbose


class PluginManager:
    def __init__(self, plugins: list[type(BasePlugin)], kwargs: dict, verbose: ResponseVerbose, options: list[str]):
        self._plugins_cls = {
            plugin.name: plugin for plugin in plugins
        }
        if len(self._plugins_cls) != len(plugins):
            raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail=f'Repeating options')
        self._kwargs = kwargs
        self._options = options
        self._verbose = verbose

        self._plugins_obj = {}
        self._responses = {}
        self._results = {}

    def get_plugin(self, name: str) -> BasePlugin:
        if name not in self._plugins_obj:
            plugin_cls = self._plugins_cls[name]
            self._plugins_obj[name] = self._create_plugin(plugin_cls)
        return self._plugins_obj[name]

    def get_plugin_response(self, name) -> dict:
        if name not in self._responses:
            self._responses[name] = self.get_plugin(name).response()
        return self._responses[name]

    def get_plugin_result(self, name) -> typing.Any:
        if name not in self._results:
            self._results[name] = self.get_plugin(name).result()
        return self._results[name]

    def execute(self) -> dict:
        response = {}
        for option in self._options:
            if option not in self._plugins_cls:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Unknown option: {option}')
            result = self.get_plugin_response(option)
            response[option] = result
        return response

    def _create_plugin(self, plugin_cls: type(BasePlugin)):
        plugin = plugin_cls(manager=self, verbose=self._verbose, **self._kwargs)
        plugin.init()
        return plugin

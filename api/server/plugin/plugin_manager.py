import logging
import typing

from fastapi import HTTPException, status

from server.exceptions import WrongInputError, ServerError
from server.plugin.plugin import BasePlugin, InputPlugin
from server.types import ResponseVerbose


logger = logging.getLogger()


class PluginManager:
    _plugins_cls: dict[str, type(BasePlugin)] = {}

    def __init__(self, input_plugins: list[InputPlugin], kwargs: dict, options: list[str]):
        self._kwargs = kwargs
        self._options = options
        self._input_plugins = input_plugins

        self._responses = {}

    @classmethod
    def register_plugin(cls, plugin: type(BasePlugin)):
        cls._plugins_cls[plugin.name] = plugin

    def get_plugin(self, name: str) -> BasePlugin:
        if name not in self._plugins_obj:
            if name not in self._plugins_cls:
                raise WrongInputError(f'Unknown plugin: {name}')
            plugin_cls = self._plugins_cls[name]
            self._plugins_obj[name] = self._create_plugin(plugin_cls)
        return self._plugins_obj[name]

    def call_plugin(self, option) -> typing.Optional[dict]:
        path_items = option.split('.')
        if not path_items:
            raise WrongInputError('Empty option')
        result = self.get_plugin(path_items[0])
        for path in path_items[1:]:
            if path.startswith('_'):
                raise WrongInputError("Can't access private method")
            if result is None:
                return result
            if isinstance(result, dict):
                result = result.get(result)
            elif hasattr(result, path):
                result = getattr(result, path)
                if callable(result):
                    try:
                        result = result()
                    except Exception:
                        logger.exception('Option method executing')
                        raise ServerError(f'Method running error: {path}')
            else:
                raise WrongInputError(f'Unknown path: {path} in option: {option}')

        if isinstance(result, BasePlugin):
            return result.response()
        return result

    def execute(self) -> dict:
        response = {}
        for option in self._options:
            name = option.split('.')[0]
            response[name] = self.call_plugin(option)
        return response

    def _create_plugin(self, plugin_cls: type(BasePlugin)):
        plugin = plugin_cls(manager=self, verbose=self._verbose, **self._kwargs)
        plugin.init()
        return plugin

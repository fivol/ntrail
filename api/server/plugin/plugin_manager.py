import logging
import typing

from server.exceptions import WrongInputError, ServerError
from server.plugin.plugin import Plugin, BasePlugin

logger = logging.getLogger()


class PluginManager:
    _plugins_cls: dict[str, type(Plugin)] = {}

    def __init__(self, kwargs: dict, input_plugins: list[str], options: list[str]):
        self._kwargs = kwargs or {}
        self._options = options
        self._input_plugins = input_plugins

        self._responses = {}

    @classmethod
    def register_plugin(cls, plugin: type(Plugin)):
        cls._plugins_cls[plugin.name] = plugin

    def call_plugin(self, option) -> typing.Optional[dict]:
        path_items = option.split('.')
        if not path_items:
            raise WrongInputError('Empty option')
        result = self._create_plugin(path_items[0])
        for path in path_items[1:]:
            if path.startswith('_'):
                raise WrongInputError("Can't access private method")
            if result is None:
                break
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
            result = result.response()
        return result

    def execute(self) -> dict:
        response = {}
        for plugin in self._input_plugins:
            self._run_input_plugin(plugin)

        for option in self._options:
            name = option.split('.')[0]
            response[name] = self.call_plugin(option)
        return response

    def _create_plugin(self, name: str):
        plugin_cls = self.get_plugin(name)
        plugin = plugin_cls(manager=self, **self._kwargs)
        plugin.init()
        return plugin

    def get_plugin(self, name):
        try:
            return self._plugins_cls[name]
        except KeyError:
            raise WrongInputError(f'Unknown plugin: {name}')

    def _run_input_plugin(self, name: str):
        try:
            kwargs = self.get_plugin(name).read(**self._kwargs)
            self._kwargs.update(kwargs)
        except TypeError as e:
            raise WrongInputError(f'Incorrect input: {e}')

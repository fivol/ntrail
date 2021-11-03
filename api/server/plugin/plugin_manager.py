import logging
import typing

from server.exceptions import WrongInputError, ServerError
from server.plugin.plugin import Plugin, BasePlugin, InputPlugin

logger = logging.getLogger()


class PluginManager:
    _plugins_cls: dict[str, type(Plugin)] = {}

    def __init__(self, kwargs: dict, input_plugins: list[str], options: list[str]):
        self._kwargs = kwargs or {}
        self._options = options
        self._input_plugins = input_plugins

        self._responses = {}

    @staticmethod
    def _plugin_name(plugin):
        return PluginManager._full_plugin_name(plugin.name, is_input=issubclass(plugin, InputPlugin))

    @staticmethod
    def _full_plugin_name(name: str, is_input: bool) -> str:
        if is_input:
            return f'input.{name}'
        return f'plugin.{name}'

    @classmethod
    def register_plugin(cls, plugin: type(Plugin)):
        cls._plugins_cls[cls._plugin_name(plugin)] = plugin

    def call_plugin(self, option) -> typing.Optional[dict]:
        path_items = option.split('.')
        if len(path_items) > 2:
            raise WrongInputError(f'Incorrect option (too many dots): {option}')
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

    @staticmethod
    def _add_result(response: dict, option: str, result: dict):
        response[option] = result
        return response

    def execute(self) -> dict:
        response = {}
        for plugin in self._input_plugins:
            self._run_input_plugin(plugin)

        for option in self._options:
            result = self.call_plugin(option)
            response = self._add_result(response, option, result)

        return response

    def _create_plugin(self, name: str):
        plugin_cls = self.get_plugin(name, is_input=False)
        plugin = plugin_cls(manager=self, **self._kwargs)
        plugin.init()
        return plugin

    def get_plugin(self, name, is_input=False):
        try:
            return self._plugins_cls[self._full_plugin_name(name, is_input)]
        except KeyError:
            raise WrongInputError(f'Unknown plugin: {name}')

    def _run_input_plugin(self, name: str):
        try:
            kwargs = self.get_plugin(name, is_input=True).read(**self._kwargs)
            self._kwargs.update(kwargs)
        except TypeError as e:
            raise WrongInputError(f'Incorrect input: {e}')

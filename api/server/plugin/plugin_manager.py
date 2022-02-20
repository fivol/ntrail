import asyncio
import inspect
import logging
import typing

from server.exceptions import NtrailWrongInputError, NtrailServerError, NtrailBaseException
from server.plugin.plugin import Plugin, BasePlugin, InputPlugin
from worker.parsers.exceptions import AccessApiException, AccessFactoryException
from loguru import logger


class PluginManager:
    _plugins_cls: dict[str, type(Plugin)] = {}

    def __init__(self, kwargs: dict, input_plugins: list[str], options: list[str], namespace=None):
        self._kwargs = kwargs or {}
        self._options = options
        self._input_plugins = input_plugins
        self._namespace = namespace

        self._responses = {}

    @classmethod
    def _plugin_name(cls, plugin):
        return cls._full_plugin_name(plugin.name, is_input=issubclass(plugin, InputPlugin), namespace=plugin.namespace)

    @classmethod
    def _full_plugin_name(cls, name: str, is_input: bool, namespace) -> str:
        namespace = namespace or 'none'
        if is_input:
            return f'input.{namespace}{name}'
        return f'plugin.{namespace}.{name}'

    @classmethod
    def register_plugin(cls, plugin: type(Plugin)):
        cls._plugins_cls[cls._plugin_name(plugin)] = plugin

    async def call_plugin(self, option) -> typing.Optional[dict]:
        path_items = option.split('.')
        if len(path_items) > 2:
            raise NtrailWrongInputError(f'Incorrect option (too many dots): {option}')
        if not path_items:
            raise NtrailWrongInputError('Empty option')
        result = await self._create_plugin(path_items[0])
        if result.broken:
            return None
        for path in path_items[1:]:
            if path.startswith('_'):
                raise NtrailWrongInputError("Can't access private method")
            if result is None:
                break
            if isinstance(result, dict):
                result = result.get(result)
            elif hasattr(result, path):
                result = getattr(result, path)
                if callable(result):
                    try:
                        result = result()
                        if inspect.isawaitable(result):
                            result = await result
                    except NtrailBaseException:
                        raise
                    except AccessApiException:
                        raise
                    except Exception:
                        logger.exception('Option method executing')
                        raise NtrailServerError(f'Method running error: {path}')
            else:
                raise NtrailWrongInputError(f'Unknown path: {path} in option: {option}')

        if isinstance(result, BasePlugin):
            result = result.response()
            if inspect.isawaitable(result):
                result = await result  # noqa
        return result

    @staticmethod
    def _add_result(response: dict, option: str, result):
        items = option.split('.')
        if len(items) == 1:
            plugin = items[0]
            if not isinstance(result, dict):
                response[plugin] = result
            else:
                response[plugin] = {**response.get(plugin, {}), **result}
        elif len(items) == 2:
            plugin, attr = items
            if plugin in response:
                response[plugin][attr] = result
            else:
                response[plugin] = {
                    attr: result
                }
        else:
            raise NtrailWrongInputError('Incorrect option format')
        return response

    async def execute(self) -> dict:
        response = {}
        try:
            for plugin in self._input_plugins:
                await self._run_input_plugin(plugin)

            results = await asyncio.gather(
                *[
                    self.call_plugin(option)
                    for option in self._options
                ], return_exceptions=True
            )
            for option, result in zip(self._options, results):
                if isinstance(result, Exception):
                    logger.exception('Plugin {} ends with exception: {}', option, result, exc_info=result)
                    if isinstance(result, NtrailBaseException):
                        raise result
                    result = None
                response = self._add_result(response, option, result)

        except NtrailBaseException:
            raise
        except AccessFactoryException as e:
            raise NtrailServerError(str(e))

        return response

    async def _create_plugin(self, name: str) -> BasePlugin:
        plugin_cls = self.get_plugin(name, is_input=False)
        plugin = plugin_cls(manager=self, **self._kwargs)
        await plugin.init()
        return plugin

    def get_plugin(self, name, is_input=False):
        try:
            return self._plugins_cls[self._full_plugin_name(name, is_input, namespace=self._namespace)]
        except KeyError:
            raise NtrailWrongInputError(f'Unknown plugin: {name}')

    async def _run_input_plugin(self, name: str):
        try:
            kwargs = await self.get_plugin(name, is_input=True).read(**self._kwargs)
            logger.debug('Read plugin result: {}', kwargs)
            self._kwargs.update(kwargs)
        except TypeError as e:
            raise NtrailWrongInputError(f'Incorrect input: {e}')

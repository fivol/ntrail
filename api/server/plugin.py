from fastapi.exceptions import HTTPException
from fastapi import status

from server.types import ResponseVerbose


class BasePlugin:
    name: str

    def run(self):
        pass


class PluginManager:
    def __init__(self, plugins: list[type(BasePlugin)], args: dict, verbose: ResponseVerbose, options: list[str]):
        self._plugins_cls = {
            plugin.name: plugin for plugin in plugins
        }
        self._args = args
        self._options = options
        self._verbose = verbose

        self._plugins_obj = {}
        self._results = {}

    @classmethod
    def _run_plugin(cls, plugin: BasePlugin) -> dict:
        plugin.run()

    def _get_plugin(self, name: str) -> BasePlugin:
        plugin_cls = self._plugins_cls[name]
        plugin_cls()

    def execute(self, ) -> dict:
        for option in options:
            if option not in self._plugins_cls:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Unknown option: {option}')
            plugin = self._get_plugin(option)
            result = self._run_plugin(plugin)

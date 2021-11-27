from core import IGUser
from core.module.many_entities import ManyEntities
from pycommon.decors import cache_method_ignore_args

from worker import IGMethods


class IGCommunity(ManyEntities):
    _single_media_cls = IGUser

    def __init__(self, users):
        super().__init__()
        self.nodes = []
        if users:
            first = users[0]
            if isinstance(first, int):
                self.nodes = users
            elif isinstance(first, dict):
                self.nodes = [user['id'] for user in users]
                self._data = users
            else:
                raise ValueError

    @cache_method_ignore_args
    async def data(self) -> list:
        return IGMethods.account.map(self.nodes)

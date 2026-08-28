from core import IGUser
from core.module.many_entities import ManyEntities
from pycommon.decors import cache_method_ignore_args

from worker import IGMethods


class IGCommunity(ManyEntities):
    _single_media_cls = IGUser

    def __init__(self, users=None):
        super().__init__(users)

    @cache_method_ignore_args
    async def data(self) -> list:
        return await IGMethods.account.map(self.nodes)

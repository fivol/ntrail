from worker import VKMethods
from abc import ABCMeta
from datetime import datetime

from core.module.single_entity import SingleEntity


class MediaObject(SingleEntity, metaclass=ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = None
        self.type = None

    async def likes(self):
        from core.modules.vk.vkcommunity import VKCommunity
        owner_id, item_id = self.id.split('_')
        return VKCommunity(await VKMethods.likes(type_='post', item_id=item_id, owner_id=owner_id))

    async def date(self):
        timestamp = (await self.data()).get('date')
        return timestamp and datetime.fromtimestamp(timestamp)

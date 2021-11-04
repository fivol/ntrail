from core.module.single_entity import SingleEntity
from worker import VkMethods
from abc import ABCMeta


class MediaObject(SingleEntity, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.id = None
        self.type = None

    def likes(self):
        from core.modules.vk.vkcommunity import VKCommunity
        owner_id, item_id = self.id.split('_')
        return VKCommunity(VkMethods.likes.sync(type_='post', item_id=item_id, owner_id=owner_id))

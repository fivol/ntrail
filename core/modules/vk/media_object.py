from core.module.one_object import OneObject
from core.modules.vk.vkapi import VKAPI


class MediaObject(OneObject, VKAPI):
    def __init__(self):
        super().__init__()
        self.id = None
        self.type = None

    def likes(self):
        from core.modules.vk.vkcommunity import VKCommunity
        return VKCommunity(self.get_object_likes(self.type, self.id))

from ntmodule.one_object import OneObject
from apimodule_vk.vkapi import VKAPI


class MediaObject(OneObject, VKAPI):
    def __init__(self):
        super().__init__()
        self.id = None
        self.type = None

    def likes(self):
        from module_vk.vkcommunity import VKCommunity
        return VKCommunity(self.get_object_likes(self.type, self.id))

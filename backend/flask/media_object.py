from one_object import OneObject
from vkapi import VKAPI


class MediaObject(OneObject, VKAPI):
    def __init__(self):
        super().__init__()
        self.id = None
        self.type = None

    def likes(self):
        from vkcommunity import VKCommunity
        return VKCommunity(self.get_object_likes(self.type, self.id))

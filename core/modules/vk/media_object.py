from module.single_media import SingleMedia
from modules.vk.vkapi import VKAPI


class MediaObject(SingleMedia, VKAPI):
    def __init__(self):
        super().__init__()
        self.id = None
        self.type = None

    def likes(self):
        from modules.vk.vkcommunity import VKCommunity
        return VKCommunity(self.get_object_likes(self.type, self.id))

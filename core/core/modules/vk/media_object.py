from core.module.single_media import SingleMedia


class MediaObject(SingleMedia):
    def __init__(self):
        super().__init__()
        self.id = None
        self.type = None

    def likes(self):
        from core.modules.vk.vkcommunity import VKCommunity
        return VKCommunity(self.get_object_likes(self.type, self.id))

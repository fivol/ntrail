from vkcommunity import VKCommunity
from vkuser import VKUser
from vkgroup import VKGroup
from vkgroups import VKGroups
from igcommunity import IGCommunity
from iguser import IGUser


class Person:
    def __init__(self, obj):
        self.vk = None
        self.ig = None

        if isinstance(obj, VKUser):
            self.vk = obj

        if isinstance(obj, IGUser):
            self.ig = obj

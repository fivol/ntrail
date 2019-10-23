from one_object import OneObject
from tools import once_property
from vkapi import VKAPI


class VKGroup(OneObject, VKAPI):
    def __init__(self, group):
        super().__init__()
        self.screen_name = None
        if isinstance(group, str):
            name = group.split('/')[-1]
            self.screen_name = name
            self.id = self.resolve_screen_name(name)['object_id']
        else:
            self.id = int(group)

        self.pk = self.id
        assert self.id

    @once_property
    def full_data(self):
        return self.get_group_data(self.id, full=True)

    @once_property
    def short_data(self):
        return self.get_group_data(self.id, full=False)

    @once_property
    def valid(self):
        return True

    def get_members(self, amount=1000):
        from vkcommunity import VKCommunity
        members = self.get_group_members(self.id, amount=amount)
        return VKCommunity(members)

    @once_property
    def name(self):
        return self.short_data['name']

    @once_property
    def url(self):
        return f"https://vk.com/{self.short_data['screen_name']}"

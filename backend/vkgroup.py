from baseapi import BaseAPI, once_property


class VKGroup(BaseAPI):
    def __init__(self, group):
        super().__init__()
        self.screen_name = None
        self.id = None
        if isinstance(group, str):
            try:
                self.id = int(group)
            except:
                name = group.split('/')[-1]
                self.screen_name = name
                self.id = self.resolve_screen_name(name)['object_id']
        elif isinstance(group, int):
            self.id = group
        else:
            raise TypeError('Wrong group type: {}'.format(type(group)))
        assert self.id

    @once_property
    def data(self):
        return self.get_group_data(self.id)

    def get_members(self, amount=1000):
        from community_pool import Community
        members = self.get_group_members(self.id, amount)
        return Community(members)

    def print(self, additional=''):
        print(f"{self.data['name']}    https://vk.com/{self.data['screen_name']} {additional}")

    def __hash__(self):
        return hash(self.id)

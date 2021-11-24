from core.module.single_entity import SingleEntity
from pycommon.decors import cache_method_ignore_args
from worker import IGMethods


class IGUser(SingleEntity):
    @classmethod
    async def create(cls, user):
        if isinstance(user, str):
            return cls(await IGMethods.resolve(user))
        else:
            return cls(user)

    def __init__(self, user):
        super().__init__()
        self.id = None
        self.username = None
        self.full_name = None
        self.profile_pic_url = None
        self.profile_pic_url_hd = None
        self.biography = None
        self.external_url = None
        self.follows_count = 0
        self.followed_by_count = 0
        self.media_count = 0
        self.is_private = False
        self.is_verified = False
        self.medias = []
        self.blocked_by_viewer = False
        self.country_block = False
        self.followed_by_viewer = False
        self.follows_viewer = False
        self.has_channel = False
        self.has_blocked_viewer = False
        self.highlight_reel_count = 0
        self.has_requested_viewer = False
        self.is_business_account = False
        self.is_joined_recently = False
        self.business_category_name = None
        self.business_email = None
        self.business_phone_number = None
        self.business_address_json = None
        self.requested_by_viewer = False
        self.connected_fb_page = None
        print(user)
        if isinstance(user, int):
            self.id = user
        elif isinstance(user, dict):
            # TODO short data and full data
            self._data = user
            self._init(user)
        else:
            raise TypeError(f'Wrong user type: {type(user)}, {user}')

    def url(self):
        return f'https://instagram.com/{self.username}/'

    @cache_method_ignore_args
    async def data(self) -> dict:
        return await IGMethods.account(self.id)

    async def followers(self, count=300):
        from core.modules.ig.igcommunity import IGCommunity
        return IGCommunity(await IGMethods.following(self.id, count=count))

    async def following(self, count=300):
        from core.modules.ig.igcommunity import IGCommunity
        return IGCommunity(await IGMethods.following(self.id, count=count))

    async def valid(self):
        pass

    def status(self):
        pass


import re

from core.helpers.utils import init_object_props
from core.module.single_entity import SingleEntity
from core.modules.ig.igpost import IGPost
from pycommon.decors import cache_method_ignore_args
from worker import IGMethods


class IGUser(SingleEntity):
    @classmethod
    async def create(cls, user):
        if isinstance(user, str):
            match = re.search(r'instagram.com/([a-zA-Z_.]+)', user)
            if match:
                user = match.group(1)
            return cls(await IGMethods.resolve(user))
        else:
            return cls(user)

    def __init__(self, user):
        # Basic
        self.id = None
        self.username = None
        self.full_name = None
        self.profile_pic_url = None
        self.is_private = False
        self.is_verified = False
        # Advanced
        self.profile_pic_url_hd = None
        self.biography = None
        self.external_url = None
        self.follows_count = 0
        self.followed_by_count = 0
        self.media_count = 0
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

        super().__init__(user)

    @property
    def url(self):
        return f'https://instagram.com/{self.username}/'

    @cache_method_ignore_args
    async def data(self) -> dict:
        data = await IGMethods.account(self.id)
        init_object_props(self, data)
        return data

    async def followers(self, count=300):
        from core.modules.ig.igcommunity import IGCommunity
        return IGCommunity(await IGMethods.followers(self.id, count=count))

    async def following(self, count=300):
        from core.modules.ig.igcommunity import IGCommunity
        return IGCommunity(await IGMethods.following(self.id, count=count))

    async def wall(self, count=20) -> list[IGPost]:
        posts = await IGMethods.wall(self.id, count=count)
        return [IGPost(post) for post in posts]

    async def valid(self):
        return isinstance(self.username, str) and self.username

    def status(self):
        pass

    def __repr__(self):
        return f"IGUser('{self.username or self.id}')"


from core.helpers.utils import init_object_props
from worker import IGMethods


class IGPostMedia:
    def __init__(self, media):
        self.id = None
        self.dimensions = None
        self.display_url = None
        self.is_video = None
        self.comments_disabled = None
        self.taken_at_timestamp = None
        init_object_props(self, media)

    def __repr__(self):
        return f'IGPostMedia<{self.id}>({self.display_url})'


class IGPost:
    def __init__(self, post, *args, **kwargs):
        if 'edge_sidecar_to_children' in post:
            self.medias = [IGPostMedia(media['node']) for media in post['edge_sidecar_to_children']['edges']]
        else:
            self.medias = [IGPostMedia(post)]
        self.id = None
        self.shortcode = None
        self.likes_count = post.get('edge_media_preview_like', {}).get('count')

        init_object_props(self, post)

    async def likes(self):
        from core import IGCommunity
        likes = await IGMethods.likes(self.shortcode)
        return IGCommunity(likes)

    def __repr__(self):
        return f'IGPost(medias: {repr(self.medias)})'

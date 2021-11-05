from functools import cache

from pycommon.decors import cache_method_ignore_args
from .media_object import MediaObject
from collections import defaultdict
from core.module.many_entities import ManyEntities
from worker import VkMethods


class VKPost(MediaObject):
    def __init__(self, post):
        super().__init__()
        self.type = 'post'
        if isinstance(post, dict):
            self.id = f'{post["owner_id"]}_{post["id"]}'
            self._data = post
        elif isinstance(post, str):
            self.id = post
        else:
            raise TypeError('Wrong post type', type(post))

    @cache_method_ignore_args
    async def data(self, force=False, full=True) -> dict:
        return (await VkMethods.posts_ids([self.id]))[0]

    def summary(self) -> dict:
        # TODO
        return {}

    @property
    async def text(self):
        return (await self.data()).get('text', '')

    @property
    def photos(self):
        return self.attachments().get('photo', [])

    @property
    def views(self):
        return self.data().get('views', {}).get('count', None)

    def attachments(self):
        atts = self.data().get('attachments', [])
        attachments = defaultdict(list)
        for attachment in atts:
            attachments[attachment['type']].append(
                attachment[attachment['type']]
            )
        return dict(attachments)

    def comments(self):
        # TODO
        return []

    @property
    def valid(self):
        return bool(self.id)

    @property
    def status(self):
        return None

    @property
    def url(self):
        return f'https://vk.com/wall{self.id}'

    @property
    def name(self):
        info = 'POST: '
        if 'copy_history' in self.data():
            info += 'REPOST '
        if self.attachments():
            info += ', '.join(self.attachments().keys()) + ' '
        if self.text:
            info += 'text: ' + self.text[:30] + ('...' if len(self.text) > 30 else '')
        return info


class VKPosts(ManyEntities):
    _single_media_cls = VKPost

    def __init__(self, posts):
        super().__init__()
        assert isinstance(posts, list)
        self.nodes = []
        if not posts:
            self.nodes = []
        else:
            if isinstance(posts[0], str):
                self.nodes = posts
            elif isinstance(posts[0], VKPost):
                self.nodes = [post.id for post in posts]
            elif isinstance(posts[0], dict):
                self.posts_dicts = posts
                self.nodes = [VKPost(post).id for post in posts]
            else:
                raise TypeError('Wrong posts type', type(posts))

    def name(self):
        return ''

    @cache
    def data(self, force=False, full=True) -> list:
        return VkMethods.posts_ids.sync_map(self.nodes)

    def summary(self) -> dict:
        return {}

    def connections(self, **kwargs) -> dict[list]:
        pass

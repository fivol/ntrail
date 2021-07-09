from .media_object import MediaObject
from .vkapi import VKAPI
from core.tools import once_property, valid_object_method
from collections import defaultdict
from core.module.many_objects import ManyObjects


class VKPost(MediaObject, VKAPI):
    def __init__(self, post):
        super().__init__()
        self.type = 'post'
        if isinstance(post, dict):
            self.full_data_ = post
            self.id = f'{post["owner_id"]}_{post["id"]}'
        elif isinstance(post, str):
            self.id = post
        else:
            raise TypeError('Wrong post type', type(post))

    def option(self, key):
        self.full_data.get(key, None)

    @once_property
    @valid_object_method
    def full_data(self):
        return self.get_posts_by_ids([self.id])[0]

    @property
    def text(self):
        return self.full_data.get('text', '')

    @property
    def images(self):
        return []

    @property
    def views(self):
        return self.full_data.get('views', {}).get('count', None)

    @once_property
    def attachments(self):
        atts = self.full_data.get('attachments', [])
        attachments = defaultdict(list)
        for attachment in atts:
            attachments[attachment['type']].append(
                attachment[attachment['type']]
            )
        return dict(attachments)

    def comments(self):
        return self.get_comments(self.id)

    @property
    def valid(self):
        return bool(self.id)

    @property
    def url(self):
        return f'https://vk.com/wall{self.id}'

    @property
    def name(self):
        info = ''
        if 'copy_history' in self.full_data:
            info += 'REPOST '
        if self.attachments:
            info += ', '.join(self.attachments.keys()) + ' '
        if self.text:
            info += 'text: ' + self.text[:30] + ('...' if len(self.text) > 30 else '')
        return info


class VKPosts(ManyObjects, VKAPI):
    base_class = VKPost

    def __init__(self, posts):
        super().__init__()
        assert isinstance(posts, list)
        self.posts_dicts = []
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

    @once_property
    def full_data(self):
        if not self.posts_dicts and self.nodes:
            self.posts_dicts = self.get_posts_by_ids(self.nodes)
        return self.posts_dicts

    def load_media_data(self, objects=None):
        # TODO Сделать норм загрузку, выглядит ужасно
        self.full_data


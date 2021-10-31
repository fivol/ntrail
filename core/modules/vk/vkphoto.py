import logging

from .media_object import MediaObject
from module.many_media import ManyMedia
from utils import once_property, valid_object_method, align_string

logger = logging.getLogger('vk-photo')


class VKAlbum(MediaObject):
    def __init__(self, album):
        super().__init__()
        if isinstance(album, str):
            self.id = album
        elif isinstance(album, dict):
            self.id = f'{album["owner_id"]}_{album["id"]}'
            self.full_data_ = album
        else:
            raise TypeError('Wrong album type')

    def photos(self):
        return VKPhotos(self.get_album_photos(self.id))

    @property
    def url(self):
        return 'https://vk.com/album' + self.id

    @once_property
    def full_data(self):
        return self.get_albums_by_ids([self.id])[0]

    @property
    def valid(self):
        return True

    @property
    def name(self):
        return f'size: {align_string(self.full_data["size"], 4)} {self.full_data["title"]}'


class VKAlbums(ManyMedia):
    base_class = VKAlbum

    def __init__(self, albums):
        super().__init__()
        assert isinstance(albums,  list)
        if not albums:
            self.nodes = []
            self.full_data_ = []
        elif isinstance(albums[0], str):
            self.nodes = albums
        elif isinstance(albums[0], VKAlbum):
            self.nodes = [album.id for album in albums]
        elif isinstance(albums[0], dict):
            self.nodes = [f'{album["owner_id"]}_{album["id"]}' for album in albums]
            self.full_data_ = albums
        else:
            raise TypeError('Wrong albums type')

    @once_property
    def full_data(self):
        if not self.nodes:
            return []
        owner = self.nodes[0].split('_')[0]
        for node in self.nodes[1:]:
            assert node.split('_')[0] == owner
        return self.get_albums_by_ids(self.nodes)

    def load_media_data(self, objects=None):
        self.full_data


class VKPhoto(MediaObject):
    def __init__(self, photo):
        super().__init__()
        self.id = None
        if isinstance(photo, dict):
            self.full_data_ = photo
            self.id = f'{photo["owner_id"]}_{photo["id"]}'
        elif isinstance(photo, str):
            self.id = photo
        else:
            raise TypeError('Wrong Photo type')

    @once_property
    def full_data(self):
        return self.get_photos_by_ids([self.id])[0]

    @property
    def url(self):
        return 'https://vk.com/photo' + self.id

    @property
    @valid_object_method
    def source(self):
        return self.full_data['sizes'][-1]['url']

    @property
    def valid(self):
        return isinstance(self.full_data, dict)

    @property
    def name(self):
        return self.source

    def tags(self):
        return self.get_photo_tags(self.id)

    def tagged_users(self):
        from .vkcommunity import VKCommunity
        return VKCommunity([int(item['user_id']) for item in self.tags()])

    def comments(self):
        pass


class VKPhotos(ManyMedia):
    base_class = VKPhoto

    def __init__(self, photos):
        super().__init__()
        assert isinstance(photos, list)
        if not photos:
            self.nodes = []
            return
        if isinstance(photos[0], str):
            self.nodes = photos
        elif isinstance(photos[0], VKPhoto):
            self.nodes = [photo.id for photo in photos]
        elif isinstance(photos[0], dict):
            self.full_data_ = photos
            self.nodes = [f'{photo["owner_id"]}_{photo["id"]}' for photo in photos]
        else:
            raise TypeError('Wrong photos type')

        if len(self.nodes) != len(set(self.nodes)):
            logger.warning('Photos nodes repeats')

    @once_property
    def full_data(self):
        return self.get_photos_by_ids(self.nodes)

    def load_media_data(self, objects=None):
        # Эта строка не бессмысленная, она подгружает full_data, которая хранится полем класса
        self.full_data

class VkParser:
    pass
    # def user(self, users_ids, fields):
    #     assert len(users_ids) <= 1000
    #     users_ids = [int(vkid) for vkid in users_ids]
    #     result = self.api.users.get(user_ids=users_ids, fields=fields)
    #     if VKError.is_error(result):
    #         return [result] * len(users_ids)
    #     assert isinstance(result, list), result
    #     if len(users_ids) != len(result):
    #         logger.warning('Fail to get several ids in user')
    #         for i, id_ in enumerate(users_ids):
    #             if i >= len(result):
    #                 result.append(VKError(INVALID_ID_ERROR).to_dict())
    #             else:
    #                 if result[i].get('id') != id_:
    #                     result.insert(i, VKError(INVALID_ID_ERROR).to_dict())
    #     return result
    #
    # def user_full(self, users_ids):
    #     return self.user(users_ids, fields=users_full_fields)
    #
    # def user_short(self, users_ids):
    #     return self.user(users_ids, fields=[])
    #
    # def group_full(self, group_ids):
    #     assert len(group_ids) <= 500
    #     res = self.api.groups.getById(group_ids=group_ids, fields=groups_full_fields)
    #     return res
    #
    # def group_short(self, group_ids):
    #     assert len(group_ids) <= 500
    #     return self.api.groups.getById(group_ids=group_ids, fields=groups_full_fields)
    #
    # def apps(self, apps_id):
    #     res = api_app.apps.get(app_ids=apps_id)
    #     return res.get('items', None)
    #
    # def followers(self, user_id, offset=0, count=1000):
    #     return api_app.users.getFollowers(user_id=user_id, offset=offset, count=count)
    #
    # def subscriptions(self, user_id, offset=0):
    #     return api_app.users.getSubscriptions(user_id=user_id, offset=offset, extended=0)
    #
    # def wall(self, obj_id, count):
    #     return api_app.wall.get(owner_id=obj_id, count=count, extended=0)
    #
    # def posts(self, post_ids):
    #     return api_app.wall.getById(posts=post_ids)
    #
    # def likes(self, object_id, count):
    #     obj_type, owner_id, item_id = object_id.split('_')
    #     return api_app.likes.getList(type=obj_type, owner_id=owner_id, item_id=item_id, count=count)
    #
    # def comments(self, post, count):
    #     owner_id, post_id = post.split('_')
    #     res = api_app.wall.getComments(owner_id=owner_id, post_id=post_id,
    #                                    need_likes=1, count=count, sort='asc',
    #                                    preview_length=0)
    #     return res
    #
    # def albums(self, obj_id, ids=None):
    #     if not ids:
    #         ids = []
    #     return api_app.photos.getAlbums(owner_id=obj_id, album_ids=ids)
    #
    # def user_photos(self, user_id):
    #     return self.api.photos.getUserPhotos(user_id=user_id, extended=True, count=1000)
    #
    # def photo_tags(self, photo_id):
    #     owner_id, photo_id = photo_id.split('_')
    #     return self.api.photos.getTags(owner_id=owner_id, photo_id=photo_id)
    #
    # def albums_ids(self, albums_ids):
    #     assert albums_ids
    #     assert isinstance(albums_ids, list)
    #     owner = albums_ids[0].split('_')[0]
    #     ids = [albums_ids[0].split('_')[1]]
    #     for album in albums_ids:
    #         assert owner == album.split('_')[0]
    #         ids.append(album.split('_')[1])
    #     albums = self.albums(owner, ids=ids)
    #
    #     if VKError.is_error(albums):
    #         logger.warning('Fail to get albums by ids')
    #         return [albums] * len(albums_ids)
    #     return albums.get('items', [])
    #
    # def photos(self, album):
    #     owner_id, album_id = album.split('_')
    #     return api_app.photos.get(owner_id=owner_id, album_id=album_id, extended=True)
    #
    # def all_photos(self, owner_id, offset=0):
    #     return self.api.photos.getAll(owner_id=owner_id, extended=True, count=200, offset=offset)
    #
    # def photos_ids(self, photos_ids):
    #     assert isinstance(photos_ids, list)
    #     res = self.api.photos.getById(photos=photos_ids, extended=True)
    #     return res
    #
    # def groups(self, vkid):
    #     return self.api.groups.get(user_id=vkid)
    #
    # def search(self, string, offset=0, limit=100, filters=''):
    #     search_result = self.api.search.getHints(q=string, offset=offset,
    #                                              limit=limit, filters=filters, search_global=1)
    #     return search_result
    #
    # def members(self, group_id, count=None, offset=None):
    #     group_id = int(group_id)
    #     assert isinstance(count, int), count
    #     assert count <= 1000
    #     assert isinstance(offset, int)
    #     return api_app.groups.getMembers(group_id=group_id, offset=offset, count=count)
    #
    # def execute(self, code_string):
    #     assert isinstance(code_string, str)
    #     res = self.api.execute(code=code_string)
    #     return res
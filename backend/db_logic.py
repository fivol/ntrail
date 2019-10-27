from models import *
import hashlib
from tools import make_json_serializable


class DB:
    @classmethod
    def save_json(cls, data, target, identity, user=None, size=None):
        data = make_json_serializable(data)
        identity = make_json_serializable(identity)
        assert isinstance(data, dict)
        assert isinstance(target, str)
        if user:
            assert isinstance(user, UserModel)
        if size:
            assert isinstance(size, int)

        query_hash = hashlib.md5(str(sorted(identity)).encode()).hexdigest()
        query_hash = query_hash[:16]
        JsonModel.insert(data=data,
                         target=target,
                         identity=identity,
                         user=user,
                         size=size,
                         hash=query_hash). \
            on_conflict_ignore().execute()

    @classmethod
    def get_json_lines(cls, count, target, size=None):
        min_size = 0
        max_size = 1000
        if size and size > 10:
            min_size = size // 4 * 3
            max_size = size // 4 * 5

        res = JsonModel.select(JsonModel.data). \
            where((JsonModel.target == target) &
                  (JsonModel.size >= min_size) &
                  (JsonModel.size <= max_size)). \
            order_by(JsonModel.id.desc()). \
            limit(count).execute()
        return list([item.data for item in res])

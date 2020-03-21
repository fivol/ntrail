import peewee

from models import *
import hashlib
from ntmodule.tools import make_json_serializable
from collections import defaultdict
from glbal import logger


class DB:
    @classmethod
    def save_json(cls, target, identity, features=None,
                  data=None, user=None, size=None, save_lines=True):
        if not data:
            data = {}
        data = make_json_serializable(data)
        assert isinstance(data, dict)
        assert isinstance(target, str)
        if user:
            assert isinstance(user, UserModel)
        if size:
            assert isinstance(size, int)
        assert bool(identity)
        if isinstance(next(iter(identity)), int):
            identity_hash_string = f'{len(identity)}i{sum(identity)}{max(identity)}'
        elif isinstance(next(iter(identity)), str):
            identity_hash_string = f'{len(identity)}s{max(identity)}{min(identity)}'
        else:
            raise TypeError('Identity value')

        identity_hash = hashlib.md5(identity_hash_string.encode()).hexdigest()
        identity_hash = identity_hash[:16]
        try:
            with db.atomic():
                entity = EntityModel.create(data=data,
                                            target=target,
                                            identity=identity,
                                            user=user,
                                            size=size,
                                            identity_hash=identity_hash)
        except peewee.IntegrityError:
            entity = EntityModel.get(EntityModel.identity_hash == identity_hash)

        assert isinstance(entity, EntityModel), type(entity)
        if features:
            cls.save_features_lines(features=features, entity=entity)

    @classmethod
    def save_features_lines(cls, features, entity):
        assert isinstance(features, dict)
        assert isinstance(entity, EntityModel)
        with db.atomic():
            for key, value in features.items():
                if len(key) <= 80:
                    assert isinstance(key, str)
                    value = float(value)
                    FeatureModel.insert(
                        name=key,
                        value=value,
                        entity=entity
                    ).on_conflict_ignore().execute()
                else:
                    logger.warning('Too long key: %s size: %s', key, len(key))

    @classmethod
    def get_features_values(cls, target, names, size=None, count=200):
        assert isinstance(count, int)
        assert isinstance(target, str)
        assert isinstance(names, list)
        min_size = 1
        max_size = 10000
        if size:
            if size > 10:
                min_size = size // 4 * 3
                max_size = size // 4 * 5
            else:
                max_size = 20

        features_lines = []
        F = FeatureModel
        for name in names:
            features_lines += \
                F.select(F.name, F.value). \
                    join(EntityModel). \
                    where(
                    F.name == name,
                    EntityModel.target == target,
                    EntityModel.size >= min_size,
                    EntityModel.size <= max_size
                ). \
                    order_by(EntityModel.time.desc()).limit(count).dicts().execute()

        features_dict = defaultdict(list)
        for line in features_lines:
            features_dict[line['name']].append(line['value'])

        return dict(features_dict)

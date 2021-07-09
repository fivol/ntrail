from core.module.any_object import AnyObject
from core.module.tools import align_string, once_property
import hashlib


class OneObject(AnyObject):
    many_objects_class = None

    def __init__(self):
        self.id = None

    def get_id(self):
        return self.gen_id(self.id)

    @classmethod
    def parse_id(cls, id_):
        if not id_.startswith(cls.id_prefix):
            return None
        return int(id_[len(cls.id_prefix):])

    @classmethod
    def gen_id(cls, plain_id):
        if isinstance(plain_id, str) and plain_id.startswith(cls.id_prefix):
            return plain_id
        return cls.id_prefix + str(plain_id)

    @property
    def valid(self):
        raise NotImplementedError

    @property
    def url(self):
        raise NotImplementedError

    def print(self, extra_data=''):
        if not self.valid:
            return

        print(f'{self.hash} {align_string(self.url, 35)} {self.name} {extra_data}')

    def __hash__(self):
        return hash(self.id)

    @once_property
    def hash(self):
        obj_hash = hashlib.sha1(str(self.id).encode('UTF-8')).hexdigest()[-16:]
        return obj_hash

    def __eq__(self, other):
        return hash(other) == hash(self)

    @property
    def name(self):
        return f'{self.id}'

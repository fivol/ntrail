from any_object import AnyObject
from tools import align_string, once_property
import hashlib


class OneObject(AnyObject):
    def __init__(self):
        self.id = None

    @property
    def valid(self):
        raise NotImplementedError

    @property
    def url(self):
        raise NotImplementedError

    def print(self, extra_data=''):
        if not self.valid:
            print('This object is not valid')
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

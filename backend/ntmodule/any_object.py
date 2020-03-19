
import hashlib
from pprint import pprint
from ntmodule.tools import *


class AnyObject:
    @property
    def params(self):
        return None

    @property
    def name(self):
        return None

    def process_data(self):
        pass

    def short_info(self):
        pass

    def print_params(self):
        pprint(self.params, compact=True)

    def print_data(self):
        pprint(self.process_data(), compact=True)

    def __hash__(self):
        pass

    @once_property
    def hash(self):
        obj_id = hashlib.sha1(str(sorted(self.__hash__())).encode('UTF-8')).hexdigest()[-16:]
        set_obj(obj_id, self)
        return obj_id

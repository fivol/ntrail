
import hashlib
import typing
from pprint import pprint
from abc import abstractmethod
from utils import *


class AnyMedia:
    @abstractmethod
    def params(self):
        """
        Dict of object parameters
        All interesting properties in folding-dict form
        """
        pass

    @property
    @abstractmethod
    def name(self):
        """
        Human readable name of object
        """
        pass

    def summery(self):
        """
        Little summery about object, most important info
        """
        pass

    def print_params(self):
        pprint(self.params, compact=True)

    def print(self):
        pprint(self.data(), compact=True)

    @abstractmethod
    def __hash__(self):
        """
        All objects must implement hash method
        """
        pass

    @once_property
    def hash(self):
        str_id = str(sorted(self.__hash__())).encode('UTF-8')
        obj_id = hashlib.sha1(str_id).hexdigest()[-16:]
        set_obj(obj_id, self)
        return obj_id

    @abstractmethod
    def data(self, force=False, full=True) -> typing.Union[list, dict, None]:
        """
        Data structure about object, list or dict
        """
        pass

    def preload(self, force=False):
        self.data(force=force)

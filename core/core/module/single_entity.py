from abc import abstractmethod
import hashlib

from core.helpers.utils import init_object_props
from core.module.any_entity import AnyEntity


class SingleEntity(AnyEntity):
    """Analog to single object, but in plural.
    User -> Users
    Photo -> Photos and so on
    It must be real class to construct it
    """
    id = None

    def __init__(self, item, *args, **kwargs):
        if isinstance(item, int) or isinstance(item, str) and item.isnumeric():
            self.id = item
        elif isinstance(item, dict):
            # TODO short data and full data
            self._data = item
            init_object_props(self, item)
        elif isinstance(item, self.__class__):
            self._data = item._data
            init_object_props(self, item._data)
        elif item is not None:
            raise TypeError(f'Wrong user type: {type(item)}, {item}')

    @property
    @abstractmethod
    def valid(self):
        """Is obj valid (exist and connected with real (social network object))
        For example, user with such id exist and so on
        """
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    async def data(self) -> dict:
        pass

    @property
    def hash(self):
        obj_hash = hashlib.sha1(str(self.id).encode('UTF-8')).hexdigest()[-16:]
        return obj_hash

    def __repr__(self):
        return f'{self.__class__.__name__}({self.id})'

    def __eq__(self, other):
        return hash(other) == hash(self)

    def __hash__(self):
        return hash(self.id)

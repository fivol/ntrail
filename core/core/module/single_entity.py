from abc import abstractmethod
import hashlib

from core.module.any_entity import AnyEntity


class SingleEntity(AnyEntity):
    """Analog to single object, but in plural.
    User -> Users
    Photo -> Photos and so on
    It must be real class to construct it
    """

    def __init__(self, *args, **kwargs):
        self.id = None

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

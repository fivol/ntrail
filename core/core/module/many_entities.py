from abc import abstractmethod
import hashlib

from collections import Counter
import random
from core.module.any_entity import AnyEntity
from core.helpers.utils import counter_top
from pycommon.decors import cache_method_ignore_args


class ManyEntities(AnyEntity):
    _single_media_cls = None

    def __init__(self, *args, **kwargs):
        self.nodes: list = []
        self._counter = None

    @property
    def size(self):
        return len(self.nodes)

    @property
    def hash(self):
        return hashlib.sha1(str(sorted(self.nodes)).encode('UTF-8')).hexdigest()[-16:]

    @cache_method_ignore_args
    def counter(self) -> Counter:
        return Counter(self.nodes)

    def objects(self):
        return [self.__class__._single_media_cls(node) for node in self.nodes]

    @abstractmethod
    def connections(self, **kwargs) -> dict[list]:
        """
        Connections between nodes dict.
        List consists of ids
        """
        pass

    def select(self, k=-1, break_point=1, rand=False):
        if rand and k > 0:
            nodes = self.nodes
            random.shuffle(nodes)
            nodes = self.nodes[:k]
            return self.__class__(nodes)

        if k == -1:
            return self.__class__(Counter(dict(counter_top(self.counter.most_common(), break_point))))
        return self.__class__(Counter(dict(self.counter.most_common(k))))

    def clusters(self):
        from core.module.clusters import Clusters
        return Clusters(self)

    def __len__(self):
        return self.size

    def __add__(self, other):
        assert self._single_media_cls == other._single_media_cls, 'You trying to sum different classes'
        return self.__class__(self.counter() + other.counter())

    def __getitem__(self, key):
        assert isinstance(key, int), key
        return self.objects()[key]

    def __or__(self, other):
        return self.__class__(list(set(self.nodes) | set(other.nodes)))

    def __and__(self, other):
        return self.__class__(list(set(self.nodes) & set(other.nodes)))

    def __repr__(self):
        return f'{self.__class__.__name__}(<size: {self.size}>)'

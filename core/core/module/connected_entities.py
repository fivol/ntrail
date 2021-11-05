from abc import ABCMeta, abstractmethod

from core.module.many_entities import ManyEntities


class ConnectedEntities(ManyEntities, metaclass=ABCMeta):
    def clusters(self):
        from core.module.clusters import Clusters
        return Clusters(self)

    @abstractmethod
    def connections(self, **kwargs) -> dict[list]:
        """
        Connections between nodes dict.
        List consists of ids
        """
        pass

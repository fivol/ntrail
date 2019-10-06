from baseapi import BaseAPI
from tools import once_property
from collections import Counter
import networkx as nx
import random


class ManyObjects(BaseAPI):
    def print(self, k=50, shuffle=False):
        objects = sorted(self.objects, key=lambda x: -self.counter[x.pk])
        if k:
            objects = objects[:k]

        self.load_media_data(objects)

        if shuffle:
            random.shuffle(objects)
        for obj in objects:
            if self.counter[obj.pk] != 1:
                obj.print(self.counter[obj.pk])
            else:
                obj.print()

    @once_property
    def objects(self):
        return [self.base_class(username) for username in self.nodes]

    def select(self, k=-1, break_point=1, rand=False):
        if rand and k > 0:
            nodes = self.nodes
            random.shuffle(nodes)
            nodes = self.nodes[:k]
            return self.__class__(nodes)

        if k == -1:
            return self.__class__(Counter(dict(self.counter_top(self.counter.most_common(), break_point))))
        return self.__class__(Counter(dict(self.counter.most_common(k))))

    def __add__(self, other):
        return self.__class__(self.counter + other.counter)

    def graph(self, **kwargs):
        g = nx.Graph()
        connections = self.get_connections(**kwargs)
        g.add_nodes_from(self.nodes)
        for node in self.nodes:
            links = connections.get(node, None)
            if links:
                g.add_edges_from([(node, link) for link in links if link in self.nodes])
        return g

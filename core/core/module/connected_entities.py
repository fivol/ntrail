import random
from abc import ABCMeta, abstractmethod
from collections import Counter
import networkx as nx

from core.module.many_entities import ManyEntities


class GraphSplitter:

    @classmethod
    def algorithm_local_moving(cls, graph):
        import numpy as np

        # TODO Проблема с импортом модуля, разобраться
        edges = np.array(graph.edges)
        mo = ModularityOptimzer(edges)
        graph_communities = mo(algorithm='local_moving')
        nodes = np.sort(np.array(graph.nodes))
        nodes = list(zip(nodes, graph_communities))
        communities_lists = {}
        for id, com in nodes:
            communities_lists[com] = communities_lists.get(com, []) + [id]
        communities_list = list(communities_lists.values())

        return communities_list

    @classmethod
    def algorithm_label_propagation(cls, graph):
        node_group = dict([(node, i) for i, node in enumerate(graph.nodes)])
        new_node_group = {}
        nodes = graph.nodes
        for ii in range(min(len(node_group) * 10, 1000)):
            for node in random.sample(nodes, len(nodes)):
                ne_groups = Counter(
                    dict(
                        [
                            (node_group[nei], graph.edges[(node, nei)].get('weight', 1))
                            for nei in graph.neighbors(node)
                        ]
                    )
                )
                if ne_groups:
                    new_group = ne_groups.most_common(1)[0][0]
                    new_node_group[node] = new_group
            node_group = new_node_group.copy()
        categories = {}
        for key, value in node_group.items():
            categories[value] = categories.get(value, []) + [key]
        return list(categories.values())

    @classmethod
    def algorithm_louvain(cls, graph):
        # https://github.com/taynaud/python-louvain
        import community
        partition = community.best_partition(graph)
        clusters = dict()
        for node, cls_ in partition.items():
            clusters[cls_] = clusters.get(cls_, []) + [node]
        return list(clusters.values())


class ConnectedEntities(ManyEntities, metaclass=ABCMeta):

    @abstractmethod
    async def graph(self, **kwargs) -> nx.Graph:
        """
        Connections between nodes dict.
        List consists of ids
        """
        pass

    async def pools(self, algorithm='louvain'):
        graph = await self.graph()
        if not graph.number_of_nodes() or not graph.number_of_edges():
            return []

        if algorithm == 'local_moving':
            pools = GraphSplitter.algorithm_local_moving(graph)
        elif algorithm == 'label_propagation':
            pools = GraphSplitter.algorithm_label_propagation(graph)
        elif algorithm == 'louvain':
            pools = GraphSplitter.algorithm_louvain(graph)
        else:
            raise ValueError(f'Algorithm "{algorithm}" does not available')

        not_used = set(self.nodes).difference(set(sum(pools, [])))
        pools = list(map(self.__class__, pools))
        pools += list(map(self.__class__, map(lambda x: [x], not_used)))

        result = sorted(pools, key=lambda x: len(x), reverse=True)

        return result

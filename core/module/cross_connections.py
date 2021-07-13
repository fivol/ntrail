from collections import defaultdict

from ntmodule.represent import Represent


class NodeImportance(Represent):
    def __init__(self, objects):
        self.many_objects = objects

    @property
    def hash(self):
        return self.many_objects.hash + '__node_importance'

    def get_entities(self):
        all_nodes = self.many_objects.nodes
        graph = self.many_objects.graph()
        node_cluster_dict = self.many_objects.get_node_cluster_dict()
        node_cross_cluster_connectedness = defaultdict(int)

        for node in all_nodes:
            for neighbor in graph.neighbors(node):
                if node_cluster_dict.get(node) != node_cluster_dict.get(neighbor):
                    node_cross_cluster_connectedness[node] += 1

        important_nodes = sorted(node_cross_cluster_connectedness.items(), key=lambda x: x[1], reverse=True)
        entities = [
            {
                **self.many_objects.base_class(node).get_entity(),
                'weight': importance,
            }
            for node, importance in important_nodes
        ]

        return {
            'items': entities
        }

    def get_params(self, parent=None):
        return {
            'service': 'vk',
            'type': self.__class__.__name__,
            # 'representType': 'connections',
            'count': 1,
            'id': self.hash,
            'name': 'Значимые люди',
            'query': 'хз',
            'prefix': 'vk.users',
            'parent': parent
        }


class CrossConnections(Represent):

    def __init__(self, objects):
        self.many_objects = objects

    def get_entities(self):
        all_nodes = self.many_objects.nodes
        node_cluster_dict = self.many_objects.get_node_cluster_dict()
        graph = self.many_objects.graph()
        connected_nodes = set()
        entities = []
        main_obj = self.many_objects.main
        main = None
        if main_obj:
            main = main_obj.id
        cluster_connectedness = defaultdict(int)
        for node in all_nodes:
            for neighbor in graph.neighbors(node):
                a = node_cluster_dict.get(node)
                b = node_cluster_dict.get(neighbor)
                if a != b and node != main and neighbor != main and (neighbor, node) not in connected_nodes:
                    cluster_connectedness[(min(a, b), max(a, b))] += 1
                    connected_nodes.add((node, neighbor))

        for n1, n2 in connected_nodes:
            c1 = node_cluster_dict[n1]
            c2 = node_cluster_dict[n2]
            entities.append(
                {
                    'items': [
                        self.many_objects.base_class(n1).get_entity(),
                        self.many_objects.base_class(n2).get_entity(),
                    ],
                    'weight': cluster_connectedness[(min(c1, c2), max(c1, c2))],
                    'valid': True,
                    'id': str(n1) + str(n2),
                }
            )

        entities = sorted(entities, key=lambda x: x['weight'])[:20]

        return {
            'items': entities
        }

    @property
    def hash(self):
        return self.many_objects.hash + '__inter_cluster'

    def get_params(self, parent=None):
        return {
            'service': 'vk',
            'type': self.__class__.__name__,
            'representType': 'connections',
            'count': 1,
            'id': self.hash,
            'name': 'Межкластерные связи',
            'query': 'хз',
            'prefix': 'vk.users',
            'parent': parent
        }

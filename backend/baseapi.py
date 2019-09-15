from vkapi import VKAPI
import random
from slmpy import ModularityOptimzer
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter
import pandas as pd
import matplotlib.patches as mpatches
import math
import hashlib

colors = []

colors += ['#FFFF00', '#0000FF', '#FF0000', '#00FF00', '#FF00FF', '#808000', '#00FFFF', '#800000',
           '#800080']
colors = list(set(colors))
random.shuffle(colors)

objects = {}


def once_property(func):
    @property
    def wrapper(class_obj):
        func_name = func.__name__
        class_value_name = f'{func_name}_'
        if hasattr(class_obj, class_value_name):
            return getattr(class_obj, class_value_name)
        method_result = func(class_obj)
        setattr(class_obj, class_value_name, method_result)
        return method_result

    return wrapper


def self_replace(*arg_names):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # print(func.__name__, kwargs)
            for arg_name in arg_names:
                if arg_name not in kwargs:
                    obj = getattr(self, arg_name)
                    if callable(obj):
                        obj = obj()
                    kwargs[arg_name] = obj

            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class BaseAPI(VKAPI):
    @staticmethod
    def get_color(i):
        if i == 0:
            return '#000000'
        if i - 1 >= len(colors):
            return '#FFFFFF'

        return colors[i - 1]

    @classmethod
    def get_obj(cls, id):
        return objects.get(id, None)

    @classmethod
    def set_obj(cls, id, obj):
        objects[id] = obj

    @staticmethod
    def reset_colors():
        random.shuffle(colors)

    @classmethod
    def tryelse(cls, code):
        pass

    @classmethod
    def dict_from_dicts(cls, list_obj, key):
        return dict([(item[key], item) for item in list_obj])

    @classmethod
    def list_from_dicts(cls, dicts_list, key, counter=False, ignore_zero=False):
        dicts_list = filter(lambda x: key in x, dicts_list)
        result = map(lambda x: x[key], dicts_list)
        if ignore_zero:
            result = filter(lambda x: bool(x), result)
        if counter:
            return Counter(result)
        return list(result)

    def show_weighted_graph(self, graph, node_color='b', color_patches=None, save_path=None):
        # print('weighted')
        def value_to_color(x):
            x = 1 - x
            x = math.sqrt(x)
            x *= 255
            x = int(x)
            x += 50
            x = min(x, 255)
            x = max(0, x)
            color = hex(x)[2:].upper()
            if len(color) == 1:
                color += color
            return f'#{color * 3}'

        weights = np.array([d['weight'] for (u, v, d) in graph.edges(data=True)])
        ordered_weights = np.sort(weights)
        l = len(weights)
        min_ = 0  # weights.mean()  # ordered_weights[int(l / 5)]
        max_ = ordered_weights[int(l / 4 * 3)]
        weights[weights < min_] = min_
        weights[weights > max_] = max_
        weights -= min_
        weights *= 1 / (max(weights))
        # weights += 0.2
        weights[weights > 1] = 1
        # edge_colors = [value_to_color(i) for i in weights]
        # print(edge_colors)
        pos = nx.spring_layout(graph)
        plt.figure(figsize=(8, 8))
        nx.draw_networkx_nodes(graph, pos,
                               node_size=30, node_color=node_color)
        arcs = nx.draw_networkx_edges(graph, pos,
                                      edgelist=graph.edges, alpha=1, width=weights, edge_color='#000000')
        # for i, arc in enumerate(arcs):
        #     arc.set_alpha(weights[i])

        plt.axis('off')
        if color_patches:
            plt.legend(handles=color_patches)

        if save_path:
            plt.savefig(save_path, dpi=1200)
        plt.show()

    @self_replace('graph')
    def show_graph(self, graph=None, node_color='r', color_patches=None, save_path=None):
        if not graph.edges:
            return

        if 'weight' in next(iter(graph.edges(data=True)))[2]:
            self.show_weighted_graph(graph,
                                     node_color=node_color, color_patches=color_patches, save_path=save_path)
            return

        plt.figure(figsize=(8, 8))
        options = {
            'node_color': node_color,
            'node_size': 50,
            'width': 1,
            'with_labels': False,
            'font_size': 8
        }

        nx.draw(graph, **options)
        if color_patches:
            plt.legend(handles=color_patches)

        if save_path:
            plt.savefig(save_path, dpi=1200)
        plt.show()

    @self_replace('graph')
    def color_graph(self, graph=None, pools=None, save_path=None, **kwargs):
        if not pools:
            pools = self.pools(**kwargs)
        color_pool = \
            pd.Series(
                dict(
                    sum(
                        [
                            list(
                                zip(
                                    pool.nodes,
                                    [
                                        (bapi.get_color(i + 1), pool)
                                    ] * pool.size))
                            for i, pool in enumerate(pools)
                        ], []
                    )
                )
            )[
                np.array(graph.nodes)
            ].values
        color_pool = [i if isinstance(i, tuple) else (self.get_color(0), self)
                      for i in color_pool]
        color_patches = []
        color_pool_dict = dict(color_pool)
        node_colors = [i[0] for i in color_pool]
        for col in color_pool_dict.keys():
            patch = mpatches.Patch(color=col, label=color_pool_dict[col].name)
            color_patches.append(patch)

        self.show_graph(node_color=node_colors, color_patches=color_patches, save_path=save_path)

    @self_replace('graph')
    def get_k_neighbors_nodes(self, graph, k=0):
        result = []
        for node in graph.nodes:
            if len(list(graph.neighbors(node))) == k:
                result.append(node)

        return result

    @self_replace('graph')
    def pools(self, graph=None, algorithm='local_moving'):
        communities = self.communities_from_graph(graph, algorithm)
        pools = [self.__class__(pool) for pool in communities]
        return pools

    @classmethod
    def communities_from_graph(cls, graph, algorithm):

        if not graph.number_of_nodes() or not graph.number_of_edges():
            return []

        def algorithm_local_moving():
            edges = np.array(graph.edges)
            mo = ModularityOptimzer(edges)
            communities = mo(algorithm='local_moving')
            nodes = np.sort(np.array(graph.nodes()))
            nodes = list(zip(nodes, communities))
            communities_lists = {}
            for id, com in nodes:
                communities_lists[com] = communities_lists.get(com, []) + [id]
            communities_list = list(communities_lists.values())

            return communities_list

        def algorithm_label_propagation():
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

        def algorithm_louvain():
            # https://github.com/taynaud/python-louvain
            import community
            partition = community.best_partition(graph)
            clusters = dict()
            for node, cls_ in partition.items():
                clusters[cls] = clusters.get(cls_, []) + [node]
            return clusters.values()

        if algorithm == 'local_moving':
            communities = algorithm_local_moving()
        elif algorithm == 'label_propagation':
            communities = algorithm_label_propagation()
        elif algorithm == 'louvain':
            communities = algorithm_louvain()
        else:
            raise ValueError(f'Algorithm "{algorithm}" does not available')

        res = sorted(communities, key=lambda x: -len(x))

        return res

    def __hash__(self):
        return hash((*sorted(self.nodes),))

    @once_property
    def id(self):
        obj_id = hashlib.sha1(str(self.__hash__()).encode('UTF-8')).hexdigest()[-3:]
        self.set_obj(obj_id, self)
        return obj_id

    @once_property
    def name(self):
        return f'{self.short_info} id: {self.id} size: {self.size}'


bapi = BaseAPI()

import bisect
# from slmpy import ModularityOptimzer
from netmodule.any_object import AnyObject
from netmodule.clusters import Clusters
from netmodule.tools import once_property, counter_top, get_color, cache_method
from collections import Counter
import networkx as nx
import random
from netmodule.tools import self_replace
import numpy as np
import re
from db_logic import DB
import matplotlib.pyplot as plt
from time import time
import pandas as pd
import matplotlib.patches as mpatches
import hashlib


class ManyObjects(AnyObject):
    def __init__(self):
        self.base_class = None
        self.counter = None
        self.nodes = None

    @property
    def size(self):
        return len(self.nodes)

    def load_media_data(self, objects=None):
        raise NotImplementedError

    def get_connections(self, **kwargs):
        return {}

    def get_id_prefix(self):
        return self.__class__.base_class.id_prefix

    @classmethod
    def communities_from_graph(cls, graph_, algorithm, remove_node=None):

        if not graph_.number_of_nodes() or not graph_.number_of_edges():
            return []

        graph = graph_.copy()
        if remove_node:
            graph.remove_node(remove_node)

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
                clusters[cls_] = clusters.get(cls_, []) + [node]
            return list(clusters.values())

        if algorithm == 'local_moving':
            communities = algorithm_local_moving()
        elif algorithm == 'label_propagation':
            communities = algorithm_label_propagation()
        elif algorithm == 'louvain':
            communities = algorithm_louvain()
        else:
            raise ValueError(f'Algorithm "{algorithm}" does not available')

        if remove_node:
            communities.append([remove_node])

        res = sorted(communities, key=lambda x: -len(x))

        return res

    def print(self, k=50, shuffle=False):
        head_line = f'Class: {self.__class__}. Size: {self.size}'
        print(head_line)
        if len(self.nodes) != len(set(self.nodes)):
            print('Nodes repeats')
        if self.counter:
            objects = sorted(self.objects, key=lambda x: -self.counter[x.id])
        else:
            objects = self.objects
        if k:
            objects = objects[:k]

        self.load_media_data(objects)

        if shuffle:
            random.shuffle(objects)
        for obj in objects:
            if self.counter and self.counter[obj.id] != 1:
                obj.print(self.counter[obj.id])
            else:
                obj.print()

    @self_replace('graph')
    def pools(self, graph=None, algorithm='louvain'):
        main_user = None
        if hasattr(self, 'main_user') and self.main_user:
            main_user = self.main_user.id
        communities = self.communities_from_graph(graph, algorithm, remove_node=main_user)
        pools = [self.__class__(pool) for pool in communities]
        return pools

    def __hash__(self):
        return hash(str(sorted(self.nodes)))

    @once_property
    def hash(self):
        obj_hash = hashlib.sha1(str(sorted(self.nodes)).encode('UTF-8')).hexdigest()[-16:]
        return obj_hash

    def get_ids(self):
        return [self.__class__.base_class.gen_id(id_) for id_ in self.nodes]

    @once_property
    def objects(self):
        data_dict = self.data_dict()
        return [self.__class__.base_class(data_dict[node]) for node in self.nodes]

    @cache_method
    def data_list(self, force=False):
        raise NotImplementedError()

    @cache_method
    def data_dict(self, force=False):
        data = self.data_list(force)
        return {
            item['id']: item
            for item in data
        }

    def preload(self, force):
        self.data_list(force)

    def select(self, k=-1, break_point=1, rand=False):
        if rand and k > 0:
            nodes = self.nodes
            random.shuffle(nodes)
            nodes = self.nodes[:k]
            return self.__class__(nodes)

        if k == -1:
            return self.__class__(Counter(dict(counter_top(self.counter.most_common(), break_point))))
        return self.__class__(Counter(dict(self.counter.most_common(k))))

    def graph(self, **kwargs):
        g = nx.Graph()
        connections = self.get_connections(**kwargs)
        g.add_nodes_from(self.nodes)
        for node in self.nodes:
            links = connections.get(node, None)
            if links:
                g.add_edges_from([(node, link) for link in links if link in self.nodes])
        return g

    def __add__(self, other):
        assert other.base_class == self.base_class
        return self.__class__(self.counter + other.counter)

    def __getitem__(self, key):
        assert isinstance(key, int), key
        return self.objects[key]

    def __or__(self, other):
        return self.__class__(list(set(self.nodes) | set(other.nodes)))

    def __and__(self, other):
        return self.__class__(list(set(self.nodes) & set(other.nodes)))

    @staticmethod
    def get_value_by_path(data, full_path):
        path_elements = full_path.split('.')
        obj = data
        for key in path_elements:
            obj = obj[key]
        return obj

    @self_replace('graph')
    def get_k_neighbors_nodes(self, graph, k=0):
        result = []
        for node in graph.nodes:
            if len(list(graph.neighbors(node))) == k:
                result.append(node)

        return result

    def color_graph(self, graph=None, sizes=False, pools=None, save_path=None, **kwargs):
        if not pools:
            pools = self.pools(**kwargs)
        if not graph:
            graph = self.graph()
        if len(graph.nodes) <= 1:
            graph = nx.Graph()

        color_pool = \
            pd.Series(
                dict(
                    sum(
                        [
                            list(
                                zip(
                                    pool.nodes,
                                    [
                                        (get_color(i + 1, len(pool.nodes)), pool)
                                    ] * pool.size))
                            for i, pool in enumerate(pools)
                        ], []
                    )
                )
            )[
                np.array(graph.nodes)
            ].values
        color_pool = [i if isinstance(i, tuple) else (get_color(0), self)
                      for i in color_pool]
        color_patches = []
        color_pool_dict = dict(color_pool)
        node_colors = [i[0] for i in color_pool]
        for col in color_pool_dict.keys():
            patch = mpatches.Patch(color=col, label=color_pool_dict[col].name)
            color_patches.append(patch)

        self.show_graph(node_color=node_colors, sizes=sizes, color_patches=color_patches, save_path=save_path)

    def show_weighted_graph(self, graph, sizes=False, node_color='b',
                            color_patches=None, save_path=None):
        from module_vk.vkgroup import VKGroups

        weights = np.array([d['weight'] for (u, v, d) in graph.edges(data=True)])
        ordered_weights = np.sort(weights)
        l = len(weights)
        min_ = 0  # weights.mean()  # ordered_weights[int(l / 5)]
        max_ = ordered_weights[int(l / 4 * 3)]
        weights[weights < min_] = min_
        weights[weights > max_] = max_
        weights -= min_
        weights *= 1 / (max(weights))
        weights[weights > 1] = 1
        node_sizes = 50
        if isinstance(self, VKGroups) and sizes:
            groups_dict = self.dict_from_dicts(self.groups_base_data(), 'id')

            def get_node_size(members_count):
                return members_count ** (1 / 2.7)
                # return math.log(members_count) * 5

            node_sizes = [get_node_size(groups_dict[id].get('members_count', 1))
                          for id in graph.nodes]

        pos = nx.spring_layout(graph)
        plt.figure(figsize=(10, 10))
        nx.draw_networkx_nodes(graph, pos, node_shape='o',
                               node_size=node_sizes,
                               node_color=node_color, with_labels=True)
        nx.draw_networkx_edges(graph, pos,
                               edgelist=graph.edges, alpha=1, width=weights, edge_color='#000000')
        plt.axis('off')
        if color_patches:
            plt.legend(handles=color_patches)

        if not save_path:
            save_path = f'data/weighted_graph_{int(time())}.svg'
        plt.savefig(save_path, dpi=1200)
        plt.show()

    @self_replace('graph')
    def show_graph(self, graph=None, node_color='r', sizes=False, color_patches=None, save_path=None):
        if len(graph.edges) and 'weight' in next(iter(graph.edges(data=True)))[2]:
            # print('WEIGHTED')
            self.show_weighted_graph(graph, sizes=sizes,
                                     node_color=node_color, color_patches=color_patches, save_path=save_path)
            return

        plt.figure(figsize=(8, 8))
        options = {
            'node_color': node_color,
            'width': 1,
            'with_labels': False,
            'font_size': 8,
            'node_size': 50
        }

        nx.draw(graph, **options)
        if color_patches:
            plt.legend(handles=color_patches)

        if not save_path:
            save_path = f'data/graph_{int(time())}.svg'
        plt.savefig(save_path, dpi=1200)
        plt.show()

    @classmethod
    def get_common_features(cls, data, category_frequency_features=None,
                            plain_features=None, frequency_features=None):
        if not data:
            return {}
        if not data['size']:
            return {}

        features = {}
        assert isinstance(data, dict)
        plain_features_attributes = {
            'mean', 'median', 'fourth', 'fourth2',
            'common_mean', 'common_median',
            'max', 'min'
        }
        frequency_features_attributes = {
            'count', 'all_count'
        }

        counter_common_list_attribute = 'common_list'
        size = data['size']
        features['size'] = size

        for feature_name, feature_value in data.items():
            if isinstance(feature_value, dict):
                for attr_name, attr_value in feature_value.items():
                    name = f'{feature_name}.{attr_name}'
                    if attr_name in plain_features_attributes:
                        features[name] = attr_value
                    elif attr_name in frequency_features_attributes:
                        features[name] = attr_value / size
                    elif attr_name == counter_common_list_attribute:
                        assert isinstance(attr_value, list)
                        if len(attr_value):
                            features[name] = attr_value[0][1] / size

        for feature in plain_features:
            features[feature] = cls.get_value_by_path(data, feature)
        for feature in frequency_features:
            features[feature] = cls.get_value_by_path(data, feature) / size

        for feature in category_frequency_features:
            for key, value in cls.get_value_by_path(data, feature):
                if isinstance(key, str):
                    key = re.sub('[^а-яa-z0-9]', ' ', key.lower())
                    key = '_'.join(key.split())
                else:
                    assert isinstance(key, int)
                features[f'{feature}-{key}'] = value / size

        features = {key: value for key, value in features.items() if not np.isnan(value)}
        return features

    def get_features(self):
        raise NotImplementedError

    def class_name(self):
        return type(self).__name__.lower()

    @property
    def name(self):
        return f'{self.short_info()} size: {self.size} id: {self.hash}'

    def collect_archive(self, count=200):
        assert isinstance(count, int)
        features = self.get_features()
        if not features:
            return []
        names = list(features.keys())
        archive = DB.get_features_values(self.class_name(),
                                         names=names, count=count)
        return {
            name: (value, sorted(archive.get(name, [])))
            for name, value in features.items()
        }

    def order_features(self, archive_size=200, version=0):
        assert isinstance(archive_size, int)
        assert isinstance(version, int)

        def calculate_priority(archive_list, value):
            # archive_list = sorted(list(set(archive_list)))
            ordered_list = archive_list
            if len(archive_list) < max(archive_size / 4, 50):
                return -1
            half_len = len(feature_list) // 2

            if version == 0:
                index_left = bisect.bisect_left(ordered_list, value)
                index_right = bisect.bisect_right(ordered_list, value)
                if index_left <= half_len <= index_right:
                    return 0

                return min(abs(index_left - half_len), abs(index_right - half_len)) \
                       / max(half_len, 1)
            if version == 1:
                median = ordered_list[half_len - 1]
                f1 = ordered_list[half_len // 2 - 1]
                f2 = ordered_list[half_len // 2 * 3 - 1]
                if f2 == f1:
                    return -1
                return (value - median) / (f2 - f1)

            raise NotImplementedError

        features_collection = self.collect_archive(archive_size)
        features_priority = []
        for feature_name, (feature_value, feature_list) in features_collection.items():
            if feature_list:
                priority = calculate_priority(feature_list, feature_value)
                features_priority.append((priority, feature_value, feature_name))
            else:
                features_priority.append((-1, feature_value, feature_name))

        return sorted(features_priority, reverse=True)

    def save_features(self):
        # data = self.process_data()
        features = self.get_features()
        identity = self.nodes
        DB.save_json(
            features=features,
            identity=identity,
            target=self.class_name(),
            size=self.size,
        )

    def process_data(self):
        raise NotImplementedError

    def clusters(self):
        return Clusters(self)

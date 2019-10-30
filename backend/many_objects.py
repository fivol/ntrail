from baseapi import BaseAPI
from tools import once_property, counter_top
from collections import Counter
import networkx as nx
import random
from tools import self_replace
import numpy as np
import re
from db_logic import DB


class ManyObjects(BaseAPI):
    def __init__(self):
        self.size = None
        self.base_class = None
        self.counter = None
        self.nodes = None

    def load_media_data(self, objects=None):
        raise NotImplementedError

    def get_connections(self, **kwargs):
        raise NotImplementedError

    def print(self, k=50, shuffle=False):
        head_line = f'Class: {self.__class__}. Size: {self.size}'
        print(head_line)
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

    @self_replace('graph')
    def pools(self, graph=None, algorithm='louvain'):
        main_user = None
        if hasattr(self, 'main_user') and self.main_user:
            main_user = self.main_user.id
        communities = self.communities_from_graph(graph, algorithm, remove_node=main_user)
        pools = [self.__class__(pool) for pool in communities]
        return pools

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

    @staticmethod
    def get_value_by_path(data, full_path):
        path_elements = full_path.split('.')
        obj = data
        for key in path_elements:
            obj = obj[key]
        return obj

    @classmethod
    def get_common_features(cls, data, category_frequency_features=None,
                            plain_features=None, frequency_features=None):
        if not data:
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
    
    def save_features(self):
        features = self.get_features()
        identity = self.nodes
        DB.save_json(
            data=features,
            identity=identity,
            target=type(self).__name__.lower(),
            size=self.size,
        )

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
from pprint import pprint
from tools import *
from glbal import logger


class BaseAPI:

    def show_weighted_graph(self, graph, sizes=False, node_color='b',
                            color_patches=None, save_path=None):
        from vkgroups import VKGroups


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
                return members_count ** (1/2.7)
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

    @staticmethod
    def is_good_username(username):
        if len(username) < 2:
            return False
        bad_characters = re.sub('[a-zA-Z0-9_\-.]', '', username)
        if bad_characters == '':
            return True
        # logger.debug('Find bad username: %s', username)
        return False

    @staticmethod
    def find_phones(phones_string):
        phones_string = phones_string.replace(' ', '')
        exp = r'\+?(?:(?:[0-9]{1,3}\([0-9]{3}\))|(?:[0-9]{4,6}))[0-9]{7}'
        return list(re.findall(exp, phones_string))

    @staticmethod
    def get_normal_phone_number(phone_string):
        if len(phone_string) > 20:
            return None
        numbers = re.sub('[^0-9]', '', phone_string)
        if len(numbers) == 11 and numbers[0] == '8':
            numbers = '7' + numbers[1:]

        if len(numbers) == 10:
            numbers = '7' + numbers

        if len(numbers) < 11:
            return None

        phone_code = numbers[:-10]
        if len(phone_code) > 3:
            return None

        phone = '+' + numbers
        return phone

    @self_replace('graph')
    @timeit
    def show_graph(self, graph=None, node_color='r', sizes=False, color_patches=None, save_path=None):

        if len(graph.edges) and 'weight' in next(iter(graph.edges(data=True)))[2]:
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

    def __del__(self):
        pass
        # self.save_memory()

    @self_replace('graph')
    def get_k_neighbors_nodes(self, graph, k=0):
        result = []
        for node in graph.nodes:
            if len(list(graph.neighbors(node))) == k:
                result.append(node)

        return result

    @self_replace('graph')
    @timeit
    def color_graph(self, graph=None, sizes=False, pools=None, save_path=None, **kwargs):
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

    def print_params(self):
        pprint(self.params, compact=True)

    def print_data(self):
        pprint(self.process_data(), compact=True)

    @self_replace('graph')
    # @timeit
    def pools(self, graph=None, algorithm='louvain'):
        main_user = None
        if hasattr(self, 'main_user') and self.main_user:
            main_user = self.main_user.id
        communities = self.communities_from_graph(graph, algorithm, remove_node=main_user)
        pools = [self.__class__(pool) for pool in communities]
        return pools

    @classmethod
    # @timeit
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

    def __hash__(self):
        return hash(str(sorted(self.nodes)))

    @once_property
    def hash(self):
        obj_id = hashlib.sha1(str(self.__hash__()).encode('UTF-8')).hexdigest()[-3:]
        set_obj(obj_id, self)
        return obj_id

    @once_property
    def name(self):
        return f'{self.short_info} size: {self.size} id: {self.hash}'


bapi = BaseAPI()

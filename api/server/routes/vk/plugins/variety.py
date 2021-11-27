from functools import lru_cache
import networkx as nx
import math

from server.plugin.plugin import BasePlugin


class EntitiesGraphPlugin(BasePlugin):
    name = 'graph'

    def connectedness(self):
        trs = nx.triangles(self.graph)
        ratio = math.log(1 + sum(trs.values()) / self.size)
        return ratio

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
            save_path = f'../data/graph_{int(time())}.svg'
        plt.savefig(save_path, dpi=1200)
        plt.show()

    def show_weighted_graph(self, graph, sizes=False, node_color='b',
                            color_patches=None, save_path=None):

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
        from module_vk.vkgroups import VKGroups
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
            save_path = f'../data/weighted_graph_{int(time())}.svg'
        plt.savefig(save_path, dpi=1200)
        plt.show()

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

    def get_k_neighbors_nodes(self, graph, k=0):
        result = []
        for node in graph.nodes:
            if len(list(graph.neighbors(node))) == k:
                result.append(node)

        return result

    @lru_cache(4)
    def get_node_cluster_dict(self):
        pools = self.pools()
        all_nodes = self.nodes
        clear_pools = list(filter(lambda x: x.size > 1, pools))
        clusters_nodes = sum([cluster.nodes for cluster in clear_pools], [])
        clear_pools += [self.__class__([free_node]) for free_node in set(all_nodes) - set(clusters_nodes)]

        node_cluster_dict = {node: id_ + 1 for id_, cluster in enumerate(clear_pools) for node in cluster.nodes}
        return node_cluster_dict

    @lru_cache(4)
    def pools(self, graph=None, algorithm='louvain'):
        main = None
        if hasattr(self, 'main') and self.main:
            main = self.main.id
        communities = self._communities_from_graph(graph, algorithm, remove_node=main)
        pools = [self.__class__(pool) for pool in communities]
        return pools

    def graph(self, **kwargs):
        g = nx.Graph()
        connections = self.connections(**kwargs)
        g.add_nodes_from(self.nodes)
        for node in self.nodes:
            links = connections.get(node, None)
            if links:
                g.add_edges_from([(node, link) for link in links if link in self.nodes])
        return g

    def response(self) -> dict:
        pass


def try_base_analog(func):
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        base_class = self.__class__._single_media_cls
        if base_class and func_name in base_class.available_attributes and self.size == 1:
            obj = base_class(self.data_list()[0])
            return getattr(obj, func_name)(*args, **kwargs)

        return func(self, *args, **kwargs)

    return wrapper


class VarietyPropsPlugin(BasePlugin):
    def get_sub_properties_categories(self):
        categories = {
            'school': {'min_percent': 10, 'importance': 7},
            'sex': {'min_percent': 50, 'importance': 3},
            'city': {'min_percent': 30, 'importance': 4},
            'country': {'min_percent': 70, 'importance': 2},
            'occupation_university': {'min_percent': 20, 'importance': 7},
            'university': {'min_percent': 20, 'importance': 6},
        }
        return categories

    def sub_prop_importance_metrics(self, prop):
        name = prop['name']
        prop_id = prop['id']
        category = prop_id.split('.')[1]
        prop_name = prop_id.split('.')[2]
        value_dict = prop['value']
        value = value_dict['value']
        value_type = value_dict['type']
        percent = value_dict.get('percent', 0)
        metric = 0
        categories = self.get_sub_properties_categories()

        if category in categories:
            prop_data = categories[category]
            if 'min_percent' in prop_data:
                min_percent = prop_data['min_percent']

                if percent >= min_percent:
                    metric = (percent - min_percent) / min_percent
            elif 'min_count' in prop_data:
                min_count = prop_data['min_count']

                if value >= min_count:
                    metric = (value - min_count) / min_count

            if prop_name != 'count':
                metric *= prop_data['importance']
            else:
                metric /= 10

            return metric

        return metric

    def get_properties(self):
        return {
            'all': self.get_all_properties(),
            'interesting': self.get_interesting_properties(),
            'important': self.get_important_properties(),
            'description': self.get_description()
        }

    def main_cluster_data(self, parent=None):
        return {
            'properties': self.get_properties(),
            'params': self.get_params(parent),
            'entities': self.get_entities(),
            'id': self.hash,
            'actions': self.get_actions()
        }

    def get_interesting_properties(self):
        all_props = self.get_all_properties()

        # processed_data = self.process_data()

        return sorted(merge_lists([

            [
                {
                    'id': f"{prop['id']}.{sub_prop['id']}",
                    'name': f"{prop['name']} {sub_prop['name']}",
                    'value': sub_prop['value'],
                    'ids': sub_prop['ids']
                }
                for sub_prop in prop['values']
            ]
            for prop in all_props
        ]), key=lambda prop: self.sub_prop_importance_metrics(prop), reverse=True)

    def get_important_properties(self):
        if not self.valid:
            return []
        return []

    def get_output_connections(self):
        base_class = self.__class__._single_media_cls
        return {
            base_class.gen_id(first_id): [base_class.gen_id(id_) for id_ in connected_list]
            for (first_id, connected_list) in
            self.get_connections().items()
        }

    def response(self) -> dict:
        pass

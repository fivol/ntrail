from baseapi import BaseAPI, once_property
from collections import Counter
import numpy as np
import networkx as nx
from vkgroup import VKGroup
import math


class GroupsPool(BaseAPI):
    def __init__(self, groups=None, most_common=None):
        super().__init__()
        if not groups:
            self.counter = Counter()
            self.nodes = []
            self.size = 0
            return

        if isinstance(groups, Counter):
            if most_common:
                groups = Counter(dict(groups.most_common(most_common)))
            self.counter = groups
            self.nodes = list([item for item, count in groups.most_common()])
        elif isinstance(groups, list) or isinstance(groups, set):
            groups = list(set(groups))
            if most_common:
                groups = groups[:most_common]
            if groups:
                if isinstance(groups[0], VKGroup):
                    self.nodes = [group.id for group in groups]
                elif isinstance(groups[0], int):
                    self.nodes = groups
            self.counter = Counter(self.nodes)

        self.size = len(self.nodes)

    def __add__(self, other):
        return GroupsPool(self.counter + other.counter)

    @once_property
    def groups(self):
        return [VKGroup(group_id) for group_id in self.nodes]

    def split_components(self):
        return sorted([GroupsPool(comp) for comp in nx.connected_components(self.graph)],
                      key=lambda x: -len(x.groups))

    @once_property
    def short_data(self):
        return self.get_groups_data(self.nodes, one_by_one=False)

    @once_property
    def full_data(self):
        return self.get_groups_data(self.nodes, one_by_one=True)

    def common(self, amount=50):
        return GroupsPool(Counter(dict(self.counter.most_common(amount))))

    def select_type(self, type_name):
        return GroupsPool([group['id'] for group in self.short_data if group['type'] == type_name])

    @once_property
    def graph(self):
        g = nx.Graph()
        groups = self.nodes
        for i in groups:
            g.add_node(i)
            for j in groups:
                if j != i:
                    connection_weight = self.compare_groups(i, j, k=1000)
                    if connection_weight > 0.005:
                        g.add_edge(i, j, weight=connection_weight)
        return g

    @once_property
    def links_graph(self):
        groups_data = self.full_data
        groups_names_dict = self.dict_from_dicts(groups_data, 'name')
        g = nx.Graph()
        for group_name, group_data in groups_names_dict.items():
            g.add_node(group_data['id'])
            if 'links' in group_data:
                for link in group_data['links']:
                    link_name = link['name']
                    link_group = groups_names_dict.get(link_name, None)

                    if link_group:
                        g.add_edge(group_data['id'], link_group['id'])
        return g

    def print(self, amount=None, shuffle=False):
        groups = self.groups.copy()
        self.short_data
        if shuffle and amount:
            np.random.shuffle(groups)

        for group in groups[:amount]:
            if self.counter[group.id] != 1:
                group.print(self.counter[group.id])
            else:
                group.print()

    def get_members(self, each_amount=1000):
        from community_pool import Community
        return Community(sum([group.get_members(each_amount) for group in self.groups], []))

    @once_property
    def short_info(self):
        import re
        from app_data import most_frequent_english_words, most_frequent_russian_words
        names = ' '.join([group['name'] for group in self.short_data]).lower()
        names = re.sub(r'[!@#$"\'.?,”()\-*+:;|/\\]', ' ', names)
        frequent_words = Counter(names.split()).most_common()
        if frequent_words:
            word, count = frequent_words[0]
            i = 0
            while word in most_frequent_english_words + most_frequent_russian_words \
                    and i < len(frequent_words):
                word, count = frequent_words[i]
                i += 1

            if self.size > 10:
                if count >= self.size / 5:
                    return word
            elif self.size >= 2:
                if count >= 2:
                    return word
            if self.size == 1:
                return word

        activity = self.params['pages_activity'].most_common(1)
        if activity:
            return activity[0]
        return 'None'

    def reverse(self):
        return self.order('reverse')

    def order(self, order_type='smart'):
        if order_type == 'smart':
            return GroupsPool(
                Counter(
                    dict(
                        [(group.id, self.counter[group.id] / math.log(group.data['members_count']))
                         for group in self.groups]
                    )
                )
            )
        if order_type == 'popular':
            return GroupsPool(
                Counter(
                    dict(
                        [(group.id, group.data['members_count'])
                         for group in self.groups]
                    )
                )
            )
        if order_type == 'reverse':
            return GroupsPool(self.nodes[::-1])

    @once_property
    def params(self):
        params = {}
        groups_list = self.short_data
        params['size'] = self.size
        params['age_limits'] = self.list_from_dicts(groups_list, 'age_limits', counter=True)
        params['city'] = self.list_from_dicts(self.list_from_dicts(groups_list, 'city'),
                                              'title', counter=True)
        params['country'] = self.list_from_dicts(self.list_from_dicts(groups_list, 'country'),
                                                 'title', counter=True)
        params['has_photo'] = self.list_from_dicts(groups_list, 'has_photo', counter=True)
        params['main_section'] = self.list_from_dicts(groups_list, 'main_section',
                                                      counter=True, ignore_zero=True)
        params['place'] = self.list_from_dicts(groups_list, 'title', counter=True)
        params['verified'] = self.list_from_dicts(groups_list, 'verified', counter=True)

        type_groups = self.select_type('group')
        type_pages = self.select_type('page')
        type_event = self.select_type('event')

        params['type_groups_count'] = type_groups.size
        params['type_pages_count'] = type_pages.size
        params['type_events_count'] = type_event.size

        params['pages_activity'] = self.list_from_dicts(type_pages.short_data, 'activity', counter=True)
        params['groups_activity'] = self.list_from_dicts(type_groups.short_data, 'activity', counter=True)

        return params

from baseapi import BaseAPI, once_property
from collections import Counter
import math
import numpy as np
import networkx as nx


class GroupsPool(BaseAPI):
    def __init__(self, groups_list=None, groups_counter=None):
        # print(groups_list, groups_counter)
        super().__init__()
        if not groups_list is None:
            self.groups = list(groups_list)
            self.counter = Counter(groups_list)
        elif not groups_counter is None:
            self.counter = groups_counter
            self.groups = list(groups_counter)
        self.nodes = self.groups
        self.size = len(self.groups)

    @classmethod
    def from_counter(cls, counter):
        # print(list(counter))
        return GroupsPool(groups_counter=counter)

    def split_components(self):
        return sorted([GroupsPool(comp) for comp in nx.connected_components(self.graph)], key=lambda x: -len(x.groups))

    @once_property
    def groups_data(self):
        return self.groups_base_data(one_by_one=True)

    def groups_base_data(self, one_by_one=False):
        return self.get_groups_data(self.groups, one_by_one=one_by_one)

    def most_common(self, amount):
        return [i[0] for i in self.counter.most_common(amount)]

    def from_most_common(self, amount):
        return GroupsPool(self.most_common(amount))

    def type(self, type_name):
        return [group for group in self.groups_data if group['type'] == type_name]

    @once_property
    def type_page(self):
        return self.type('page')

    @once_property
    def type_group(self):
        return self.type('group')

    @once_property
    def type_event(self):
        return self.type('event')

    @once_property
    def graph(self):
        g = nx.Graph()
        groups = self.groups
        for i in groups:
            g.add_node(i)
            for j in groups:
                if j != i:
                    connection_weight = self.compare_groups(i, j, k=1000)
                    if connection_weight > 0.005:
                        g.add_edge(i, j, weight=connection_weight)
        return g

    @once_property
    def graph_links(self):
        groups_data = self.groups_data

        # urls = sum([gr_data['links']['url'].split('/')[-1] for gr_data in groups_data if 'links' in gr_data], [])
        groups_names_dict = self.dict_from_dicts(groups_data, 'name')
        G = nx.Graph()
        for group_name, group_data in groups_names_dict.items():
            G.add_node(group_data['id'])
            if 'links' in group_data:
                for link in group_data['links']:
                    link_name = link['name']
                    link_group = groups_names_dict.get(link_name, None)

                    if link_group:
                        G.add_edge(group_data['id'], link_group['id'])
        return G

    def print(self, amount=None):
        groups = self.groups_data
        if amount:
            np.random.shuffle(groups)

        for group in groups[:amount]:
            print(f"{group['name']} {group['id']} https://vk.com/{group['screen_name']}")

    @once_property
    def short_info(self):
        activity = self.params['groups_pages_activity'].most_common(1)
        if activity:
            return activity[0]
        return 'NO Property'


    @once_property
    def params(self):

        groups_list = self.groups_data
        params = {}
        groups_ = self.type_group
        groups_len = len(groups_)
        pages_ = self.type_page
        pages_len = len(pages_)
        events_ = self.type_event
        events_len = len(events_)
        size = len(groups_list)

        params['groups_age_limits'] = self.list_from_dicts(groups_list, 'age_limits', counter=True)
        params['groups_city'] = self.list_from_dicts(self.list_from_dicts(groups_list, 'city'),
                                                     'title', counter=True)
        params['groups_country'] = self.list_from_dicts(self.list_from_dicts(groups_list, 'country'),
                                                        'title', counter=True)
        params['groups_has_photo'] = self.list_from_dicts(groups_list, 'has_photo', counter=True)
        params['groups_main_section'] = self.list_from_dicts(groups_list, 'main_section',
                                                             counter=True, ignore_zero=True)
        params['groups_place'] = self.list_from_dicts(groups_list, 'title', counter=True)
        params['groups_verified'] = self.list_from_dicts(groups_list, 'verified', counter=True)

        params['groups_groups_amount'] = groups_len
        params['groups_groups_fr'] = groups_len / size
        params['groups_pages_amount'] = pages_len
        params['groups_pages_fr'] = pages_len / size
        params['groups_events_amount'] = events_len
        params['groups_events_fr'] = events_len / size
        if not groups_len: groups_len = 1

        params['groups_pages_activity'] = self.list_from_dicts(pages_, 'activity', counter=True)

        try:
            params['groups_pages_activity_first_fr'] = \
                params['groups_pages_activity'].most_common(1)[1] / len(pages_)
        except: params['groups_pages_activity_first_fr'] = 0

        params['groups_groups_activity'] = self.list_from_dicts(groups_, 'activity', counter=True)
        params['groups_groups_activity_open'] = params['groups_groups_activity']['Открытая группа']
        params['groups_groups_activity_open_fr'] = params['groups_groups_activity_open'] / groups_len
        params['groups_groups_activity_close'] = params['groups_groups_activity']['Закрытая группа']
        params['groups_groups_activity_close_fr'] = params['groups_groups_activity_close'] / groups_len

        return params

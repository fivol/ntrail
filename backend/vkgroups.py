from many_objects import ManyObjects
from tools import once_property, get_common_texts_terms
from collections import Counter
import networkx as nx
from vkgroup import VKGroup
import math
from glbal import logger
from tools import timeit, dict_from_dicts, list_from_dicts, counter_top, prepare_list
from vkapi import VKAPI
import numpy as np


class VKGroups(ManyObjects, VKAPI):
    base_class = VKGroup

    def __init__(self, groups=None, save_features=False):
        super().__init__()

        if not groups:
            self.counter = Counter()
            self.nodes = []
            self.size = 0
            return

        if isinstance(groups, Counter):
            self.counter = groups
            self.nodes = list([item for item, count in groups.most_common()])
        elif isinstance(groups, list) or isinstance(groups, set):
            groups = list(set(groups))
            if groups:
                if isinstance(groups[0], VKGroup):
                    self.nodes = [group.id for group in groups]
                elif isinstance(groups[0], int):
                    self.nodes = groups
            self.counter = Counter(self.nodes)

        else:
            raise TypeError()

        self.size = len(self.nodes)
        if 5 < self.size < 500 and save_features:
            self.save_features()

    def split_components(self):
        return sorted([VKGroups(comp) for comp in nx.connected_components(self.graph)],
                      key=lambda x: -len(x.objects))

    @once_property
    def short_data(self):
        return self.get_groups_data(self.nodes, one_by_one=False)

    @once_property
    def full_data(self):
        return self.get_groups_data(self.nodes, one_by_one=True)

    def select_type(self, type_name):
        return VKGroups([group['id'] for group in self.short_data if group['type'] == type_name])

    def get_connections(self):
        connections = {}
        for i in self.nodes:
            connections[i] = []
            for j in self.nodes:
                if j != i:
                    connection_weight = self.compare_groups(i, j, k=1000)
                    if connection_weight > 0.005:
                        connections[i] += [j]
        return connections

    @once_property
    def links_graph(self):
        groups_data = self.full_data
        groups_names_dict = dict_from_dicts(groups_data, 'name')
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

    def get_members(self, each_amount=1000):
        from vkcommunity import VKCommunity
        return VKCommunity(sum([group.get_members(each_amount) for group in self.objects], []))

    def load_media_data(self, groups=None):
        self.short_data

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

        activity = self.params['pages_activity']
        if activity:
            return activity[0]
        return 'None'

    def reverse(self):
        return self.order('reverse')

    @timeit
    def order(self, order_type='smart'):
        if order_type == 'smart':
            self.short_data
            return VKGroups(
                Counter(
                    dict(
                        [(group.id, self.counter[group.id] / math.log(group.short_data.get('members_count', 10)))
                         for group in self.objects]
                    )
                )
            )
        if order_type == 'popular':
            self.short_data
            return VKGroups(
                Counter(
                    dict(
                        [(group.id, group.short_data.get('members_count', 10))
                         for group in self.objects]
                    )
                )
            )
        if order_type == 'reverse':
            return VKGroups(Counter(dict([(item, 1 / count) for item, count in self.counter.most_common()])))

    def process_data(self):
        params = self.params
        data = {
            'size': self.size
        }
        list_size_limit = 20
        ## Need work with links
        ## Добавить обработку сайтов - количество валидных, конкретные адреса, закономерности по именам доменов
        ## Подумать на полем counters. Сейчас оно вообще не считается (не приходит тк не использую execute)
        data['age_limits'] = {
            'all_count': len(params['age_limits']),
            'common_categories': counter_top(params['age_limits'])
        }
        data['city'] = {
            'all_count': len(params['city']),
            'common_list': counter_top(params['city'])
        }
        data['country'] = {
            'all_count': len(params['country']),
            'common_list': counter_top(params['country'])
        }
        data['has_photo'] = {
            'count': params['has_photo']
        }
        data['main_section'] = {
            'common_categories': counter_top(params['main_section'])
        }
        data['verified'] = {
            'count': params['verified']
        }
        data['members_count'] = prepare_list(params['members_count'])
        data['trending'] = {
            'count': params['trending']
        }
        data['wall'] = {
            'all_count': len(params['wall']),
            'common_categories': counter_top(params['wall'])
        }
        data['contacts'] = {
            'all_count': len(params['contacts']),
            'common_list': counter_top(params['contacts'])
        }
        data['description'] = {
            'len_median': np.median([len(item) for item in params['description']]),
            'len_mean': np.mean([len(item) for item in params['description']]),
            'common_list': get_common_texts_terms(params['description'])[:list_size_limit]
        }
        data['name'] = {
            'common_list': get_common_texts_terms(params['name'])[:list_size_limit]
        }
        data['site'] = {
            'all_count': len(params['site'])
        }
        data['start_date'] = prepare_list(params['start_date'])
        data['deactivated'] = {
            'all_count': len(params['deactivated']),
            'common_categories': counter_top(params['deactivated'])
        }
        data['type'] = {
            'groups_count': params['type_groups_count'],
            'pages_count': params['type_pages_count'],
            'events_count': params['type_events_count']
        }
        data['activity'] = {
            'pages': {
                'all_count': len(params['pages_activity']),
                'common_categories': counter_top(params['pages_activity'])[:list_size_limit]
            },
            'groups': {
                'common_categories': counter_top(params['groups_activity'])
            }
        }
        return data

    def get_features(self):
        data = self.process_data()
        assert isinstance(data, dict)
        features = self.get_common_features(
            data,
            category_frequency_features={
                'activity.pages.common_categories',
                'activity.groups.common_categories',
                'deactivated.common_categories',
                'wall.common_categories',
                'main_section.common_categories',
                'age_limits.common_categories',
            }, plain_features={
                'description.len_median',
                'description.len_mean'
            }, frequency_features={
                'activity.pages.all_count',
                'type.groups_count',
                'type.pages_count',
                'type.events_count'
            }
        )
        return features

    @once_property
    def params(self):
        logger.debug('@ get groups params')
        params = {}
        groups_list = self.full_data
        params['size'] = self.size
        params['age_limits'] = list_from_dicts(groups_list, 'age_limits', counter=True)
        params['name'] = list_from_dicts(groups_list, 'name')
        params['city'] = list_from_dicts(list_from_dicts(groups_list, 'city'),
                                         'title', counter=True)
        params['country'] = list_from_dicts(list_from_dicts(groups_list, 'country'),
                                            'title', counter=True)
        params['has_photo'] = sum(list_from_dicts(groups_list, 'has_photo'))
        params['main_section'] = list_from_dicts(groups_list, 'main_section',
                                                 counter=True, ignore_zero=True)
        params['place'] = list_from_dicts(groups_list, 'title', counter=True)
        params['verified'] = sum(list_from_dicts(groups_list, 'verified'))
        params['members_count'] = sorted(list_from_dicts(groups_list, 'members_count'), reverse=True)
        params['trending'] = sum(list_from_dicts(groups_list, 'trending'))
        params['wall'] = Counter(list_from_dicts(groups_list, 'wall')).most_common()
        links = sum(list_from_dicts(groups_list, 'links'), [])
        params['links_names'] = list_from_dicts(links, 'name', ignore_zero=True)
        params['links_urls'] = list_from_dicts(links, 'url', ignore_zero=True)
        params['contacts'] = Counter(list_from_dicts(
            sum(list_from_dicts(groups_list, 'contacts'), []), 'user_id')).most_common()
        params['description'] = list_from_dicts(groups_list, 'description', ignore_zero=True)
        params['site'] = list_from_dicts(groups_list, 'site', ignore_zero=True)
        params['start_date'] = sorted(list_from_dicts(groups_list, 'start_date', ignore_zero=True), reverse=True)
        params['deactivated'] = Counter(list_from_dicts(groups_list, 'deactivated')).most_common()
        counters = list_from_dicts(groups_list, 'counters')
        for counter_item in ['albums', 'articles', 'docs', 'photos', 'topics', 'videos']:
            params['counters_' + counter_item] = \
                sorted(list_from_dicts(counters, counter_item, ignore_zero=True), reverse=True)

        type_groups = self.select_type('group')
        type_pages = self.select_type('page')
        type_event = self.select_type('event')

        params['type_groups_count'] = type_groups.size
        params['type_pages_count'] = type_pages.size
        params['type_events_count'] = type_event.size

        params['pages_activity'] = list_from_dicts(type_pages.full_data, 'activity', counter=True)
        params['groups_activity'] = list_from_dicts(type_groups.full_data, 'activity', counter=True)

        return params

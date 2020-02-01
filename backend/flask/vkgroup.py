from constants import GROUP_STATUS_ABSENT, GROUP_STATUS_VALID, GROUP_STATUS_DEACTIVATED
from many_objects import ManyObjects
from tools import once_property, get_common_texts_terms, valid_object_method
from collections import Counter
import networkx as nx
import math
from glbal import logger
from tools import dict_from_dicts, list_from_dicts, counter_top, prepare_list
from vkapi import VKAPI
import numpy as np
from one_object import OneObject
from errors.api_errors import APIError, INVALID_ID_ERROR


class VKGroup(OneObject, VKAPI):
    def __init__(self, group):
        super().__init__()
        self.id = None
        self.status = None
        if isinstance(group, str):
            groupname = group.strip('/').split('/')[-1]
            user_dict = self.resolve_screen_name(groupname)
            if not isinstance(user_dict, dict):
                logger.info('VKGroup username does not exist "%s"', groupname)
                self.status = GROUP_STATUS_ABSENT
            elif not user_dict['type'] == 'group':
                logger.info('VKGroup username type is "%s"', user_dict['type'])
                self.status = GROUP_STATUS_ABSENT
            else:
                self.status = GROUP_STATUS_VALID
                self.id = user_dict['object_id']
        elif isinstance(group, int):
            self.id = int(group)
        else:
            raise TypeError('VKGroup wrong type', type(group))

    @once_property
    @valid_object_method
    def full_data(self):
        return self.get_group_data(self.id, full=True)

    @once_property
    def short_data(self):
        return self.get_group_data(self.id, full=False)

    @valid_object_method
    def get_members(self, count=1000):
        from vkcommunity import VKCommunity
        if count == -1:
            count = 30000
        members = self.get_group_members(self.id, count=count)
        return VKCommunity(members)

    @property
    @valid_object_method
    def name(self):
        return self.short_data['name']

    def posts(self):
        return self.get_group_posts(self.id)

    def check_status(self):
        if not self.status:
            user_data = self.short_data
            if APIError.is_error(user_data):
                if user_data.code == INVALID_ID_ERROR:
                    self.status = GROUP_STATUS_ABSENT
                else:
                    raise ValueError('VKGroup short data have unknown value:', user_data)
            else:
                assert isinstance(user_data, dict)
                if 'deactivated' in user_data:
                    self.status = GROUP_STATUS_DEACTIVATED
                else:
                    self.status = GROUP_STATUS_VALID
        return self.status

    @once_property
    def valid(self):
        status = self.check_status()
        assert not (status is None), status
        return status == GROUP_STATUS_VALID

    @property
    @valid_object_method
    def url(self):
        return f"https://vk.com/{self.short_data['screen_name']}"



class VKGroups(ManyObjects, VKAPI):
    base_class = VKGroup

    def __init__(self, groups=None, save_features=False):
        super().__init__()

        if not groups:
            self.counter = Counter()
            self.nodes = []
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

        if 5 < self.size < 500 and save_features:
            self.save_features()

    def split_components(self):
        return sorted([VKGroups(comp) for comp in nx.connected_components(self.graph)],
                      key=lambda x: -len(x.objects))

    @once_property
    def short_data(self):
        return self.get_groups_data(self.nodes, one_by_one=False)

    def only_valid(self):
        return VKGroups([group for group in self.objects if group.valid])

    @once_property
    def full_data(self):
        return self.get_groups_data(self.nodes, one_by_one=True)

    def select_type(self, type_name):
        return VKGroups([group['id'] for group in self.short_data if group['type'] == type_name])

    @classmethod
    def compare_groups(cls, group1, group2, k=3000):
        users1 = set(cls.get_random_group_members(group1, k=k))
        users2 = set(cls.get_random_group_members(group2, k=k))
        return len(users1.intersection(users2)) / k

    def graph(self):
        if hasattr(self, 'graph_'):
            return self.graph_
        k = 3000
        g = nx.Graph()
        g.add_nodes_from(self.nodes)
        group_members = {
            group_id: set(self.get_random_group_members(group_id, k=k))
            for group_id in self.nodes
        }
        for num, i in enumerate(self.nodes):
            for j in self.nodes[num + 1:]:
                users1 = group_members[i]
                users2 = group_members[j]
                connection_weight = len(users1.intersection(users2)) / k
                if connection_weight > 0.005:
                    g.add_edge(i, j, weight=connection_weight)
        self.graph_ = g
        return g

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
        frequent_words = self.process_data()['name']['common_list']

        if frequent_words:
            word, count = frequent_words[0]
            if self.size > 10:
                if count >= self.size / 5:
                    return word
            elif self.size >= 2:
                if count >= 2:
                    return word
            if self.size == 1:
                return word

        activity = self.process_data()['activity']['pages']['common_categories']
        if activity:
            return activity[0][0]
        return 'None'

    def reverse(self):
        return self.order('reverse')

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
        if hasattr(self, 'processed_data'):
            return self.processed_data

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
        self.processed_data = data
        return data

    def get_features(self):
        if hasattr(self, 'features_dict'):
            return self.features_dict
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
        self.features_dict = features
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

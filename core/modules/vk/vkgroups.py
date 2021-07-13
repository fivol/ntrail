from core.modules.vk.vkgroup import VKGroup
from more_itertools import unique_everseen

from core.constants import PLOT_CIRCULAR, PLOT_LINE
from core.module.represent import Represent
from core.module.represent_tools import RepresentTools
from core.tools import once_property, get_common_texts_terms, cache_method, get_field_values, bool_filter
from collections import Counter
import networkx as nx
import math
from core.glbal import logger
from core.tools import dict_from_dicts, prepare_list
from core.modules.vk.vkapi import VKAPI

age_limits_dict = {
    1: 'нет',
    2: '16+',
    3: '18+',
}

groups_types_dict = {
    'page': 'Публичная страница',
    'group': 'Группа',
    'event': 'Мероприятие'
}


class VKGroups(VKAPI, Represent, RepresentTools):
    base_class = VKGroup
    available_attributes = ['clusters', 'members']

    def __init__(self, groups=None, save_features=False, target=None, source=None, **kwargs):
        super().__init__()
        self.target = target
        self.source = source
        self.main = None

        if not groups:
            self.counter = Counter()
            self.nodes = []
            return

        if isinstance(groups, Counter):
            self.counter = groups
            self.nodes = list([item for item, count in groups.most_common()])
        elif isinstance(groups, list) or isinstance(groups, set):
            groups = list(unique_everseen(groups))

            if groups:
                if isinstance(groups[0], VKGroup):
                    self.nodes = [group.id for group in groups]
                elif isinstance(groups[0], int):
                    self.nodes = groups
                elif isinstance(groups[0], str) and VKGroup.parse_id(groups[0]):
                    self.nodes = [VKGroup.parse_id(group) for group in groups]
                else:
                    raise ValueError('Unknown nodes type for groups')

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
        return self.data_list()

    def only_valid(self):
        return VKGroups([group for group in self.objects if group.valid])

    def members(self):
        members_ids = []
        for group in self.nodes:
            members_ids += self.get_random_group_members(group, k=100)[:100]

        from .vkcommunity import VKCommunity
        return VKCommunity(members_ids, target='members', main=self.objects[0])

    @cache_method
    def data_list(self, force=False, full=False):
        # TODO Разобраться, нужно ли загружать полную инфу о группах, если нужно, все оптимизировать
        # А пока пусть будет заглушка, чтобы работало быстро
        return self.get_groups_data(self.nodes, one_by_one=full, force=force)

    @once_property
    def full_data(self):
        return self.data_list()

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

    def get_connections(self):
        graph = self.graph()
        return {
            node: list(graph.neighbors(node))
            for node in self.nodes
        }

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
        from module_vk.vkcommunity import VKCommunity
        return VKCommunity(sum([group.get_members(each_amount) for group in self.objects], []))

    def load_media_data(self, groups=None):
        self.short_data

    @once_property
    def short_info(self):
        frequent_words = self.process_data()['name']['source_list']
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

        activity = self.process_data()['activity']['pages']['source_list']
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
                    {
                        group.id: self.counter[group.id] / (math.log(group.short_data.get('members_count', 10) + 1))
                        for group in self.objects
                    }
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

    @once_property
    def params(self):
        logger.debug('@ get groups params')
        params = {}
        groups_list = self.full_data
        params['size'] = self.size
        params['age_limits'] = get_field_values(groups_list, 'age_limits', counter=True)
        params['name'] = get_field_values(groups_list, 'name')
        params['city'] = get_field_values(groups_list, 'city', key='title', counter=True)
        params['country'] = get_field_values(groups_list, 'country', key='title', counter=True)
        params['has_photo'] = get_field_values(groups_list, 'has_photo')
        params['main_section'] = get_field_values(groups_list, 'main_section', counter=True, clean=True)
        params['place'] = get_field_values(groups_list, 'title', counter=True)
        params['verified'] = get_field_values(groups_list, 'verified', clean=True, counter=True)
        params['members_count'] = get_field_values(groups_list, 'members_count')
        params['trending'] = get_field_values(groups_list, 'trending')
        params['wall'] = get_field_values(groups_list, 'wall')
        links = get_field_values(groups_list, 'links')
        params['links_names'] = get_field_values(links, 'name', clean=True)
        params['links_urls'] = get_field_values(links, 'url', clean=True)
        # params['contacts'] = Counter(list_from_dicts(
        #     sum(get_field_values(groups_list, 'contacts'), []), 'user_id')).most_common()
        params['description'] = get_field_values(groups_list, 'description', clean=True)
        params['site'] = get_field_values(groups_list, 'site', clean=True)
        params['start_date'] = get_field_values(groups_list, 'start_date', clean=True)
        params['deactivated'] = get_field_values(groups_list, 'deactivated', counter=True)
        # counters = get_field_values(groups_list, 'counters')
        # for counter_item in ['albums', 'articles', 'docs', 'photos', 'topics', 'videos']:
        #     params['counters_' + counter_item] = get_field_values(counters, counter_item, clean=True)

        type_groups = self.select_type('group')
        type_pages = self.select_type('page')
        type_event = self.select_type('event')

        params['type_groups_count'] = type_groups.size
        params['type_pages_count'] = type_pages.size
        params['type_events_count'] = type_event.size
        params['type'] = get_field_values(groups_list, 'type', counter=True)

        params['pages_activity'] = get_field_values(type_pages.full_data, 'activity', counter=True)
        params['groups_activity'] = get_field_values(type_groups.full_data, 'activity', counter=True)

        return params

    @cache_method
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
            # 'count': params['age_limits'].size,
            'source_list': params['age_limits'].most_common()
        }
        data['city'] = {
            # 'count': params['city'].size,
            'source_list': params['city'].most_common()
        }
        data['country'] = {
            # 'count': params['country'].size,
            'source_list': params['country'].most_common()
        }
        # data['has_photo'] = {
        #     'count': params['has_photo']
        # }
        data['main_section'] = {
            'source_list': params['main_section'].most_common()
        }
        data['verified'] = {
            'count': params['verified'].size
        }
        members_count = sorted(params['members_count'])
        data['members_count'] = {
            **prepare_list(members_count),
            'source_list': members_count
        }
        # data['trending'] = {
        #     'count': params['trending'].size
        # }
        # data['wall'] = {
        #     'all_count': len(params['wall']),
        #     'common_categories': counter_top(params['wall'])
        # }
        # data['contacts'] = {
        #     'all_count': len(params['contacts']),
        #     'common_list': counter_top(params['contacts'])
        # }
        # data['description'] = {
        #     'len_median': np.median([len(item) for item in params['description']]),
        #     'len_mean': np.mean([len(item) for item in params['description']]),
        #     'source_list': get_common_texts_terms(params['description']).most_common(list_size_limit)
        # }
        data['name'] = {
            'source_list': get_common_texts_terms(params['name']).most_common(list_size_limit)
        }
        data['site'] = {
            'count': len(params['site'])
        }
        data['start_date'] = prepare_list(params['start_date'])
        data['deactivated'] = {
            'count': params['deactivated'].size,
            'source_list': params['deactivated'].most_common()
        }
        data['type'] = {
            'groups_count': params['type_groups_count'],
            'pages_count': params['type_pages_count'],
            'events_count': params['type_events_count']
        }
        data['activity_pages'] = {
            # 'count': params['pages_activity'].size,
            'source_list': params['pages_activity'].most_common(ignore_single=True)
        }
        data['activity_groups'] = {
            'source_list': params['groups_activity'].most_common()
        }
        data['type'] = {
            'source_list': params['type'].most_common()
        }

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

    def get_all_properties(self):
        return bool_filter([
            self.gen_property_category('age_limits', 'Возрастные ограничения', [], PLOT_CIRCULAR,
                                       common_count=3, name_func=lambda x: age_limits_dict[x]),
            self.gen_property_category('city', 'Город', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category('name', 'Имя содержит', [], PLOT_CIRCULAR, common_count=10),
            self.gen_property_category('country', 'Страна', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category('members_count', 'Количество подписчиков', [], PLOT_LINE),
            self.gen_property_category('activity_pages', 'Тема публичной страницы', [], PLOT_CIRCULAR, common_count=6),
            self.gen_property_category('activity_groups', 'Тип группы', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category('type', 'Тип', [], PLOT_CIRCULAR, common_count=5, names_dict=groups_types_dict),
            # self.gen_property_category('description', 'Описание', [], PLOT_CIRCULAR, common_count=10),
            self.gen_property_category('verified', 'Верификация', [('count', 'Верифициовано')]),
        ])

    def get_name(self):
        source_list = self.process_data()['name']['source_list'] or []

        def name_from_words_list(items):
            return ', '.join(map(lambda x: x[0].get_value().capitalize(), items))

        if len(source_list) and len(source_list[0]) and source_list[0][1] <= 1:
            activity_pages = self.process_data()['activity_pages']['source_list']
            if activity_pages:
                return self.process_data()['activity_pages']['source_list'][0][0].get_value().capitalize()

        if len(source_list) >= 3:
            if source_list[2][1] > 2:
                return name_from_words_list(source_list[:3])
            elif source_list[1][1] > 2:
                return name_from_words_list(source_list[:2])
            else:
                return name_from_words_list(source_list[:1])

        return name_from_words_list(source_list[:1])

    def get_query(self):
        return f"GET vk.groups ({' '.join(self.get_ids())})"

    def get_items(self):
        return [VKGroup(group_id).get_entity() for group_id, _ in self.counter.most_common(300)]

    def get_actions(self):
        actions = self.get_template_actions(split=True)

        return actions + [
            {
                'id': 'members',
                'name': 'Получить 100 подписчиков',
                'target': 'one',
                'value': 'members',
            }
        ]

    def get_sub_properties_categories(self):
        return {
            'name': {'min_count': 2, 'importance': 5},
            'activity_pages': {'min_percent': 20, 'importance': 6},
        }

    def get_params(self, parent=None):
        return {
            'baseType': 'groups',
            'service': 'vk',
            'type': 'community',
            'fullEntitiesCount': 1,
            'id': self.hash,
            'name': self.get_name(),
            'query': self.get_query(),
            'parent': parent,
            'prefix': 'vk.groups'
        }

    def get_description(self):
        from .vkuser import VKUser
        if isinstance(self.source, VKUser):
            return f'ВК сообщества "{self.source.name}" ({self.size} шт.)'

        return f'ВК сообщества ({self.size} шт.)'

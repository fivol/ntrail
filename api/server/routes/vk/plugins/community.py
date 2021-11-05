import bisect
import datetime
import logging
import re
from itertools import groupby
from time import time

import numpy as np

from core.helpers.utils import clear_list
from server.helpers.utils import get_value_by_path
from server.routes.vk.data import vk_connections_names, life_main_dict, people_main_dict, political_dict, \
    occupation_type_dict, relatives_dict, smoking_dict, alcohol_dict, relation_dict, account_status_dict, \
    last_seen_platform_dict
from server.helpers.content_utils import get_field_values, list_from_dicts, concatenate_lists, is_good_username, \
    prepare_list, get_random_color, bool_filter, merge_lists
from server.helpers.tied_counter import TiedCounter
from server.helpers.tied_value import TiedValue, get_tied_array_size
from pycommon.decors import cache_method_ignore_args
from server.helpers.types import PlotType
from server.plugin.plugin import BasePlugin
from core import VKCommunity

logger = logging.getLogger()


class VKCommunityPlugin(BasePlugin):
    """
        Первый уровень: community.data - возвращает просто список словарей, которые возвращает АПИ ВК
        Второй уровень: community..
    """

    name = 'community'
    _proxy_attributes = ['name', 'size']

    def __init__(self, community: VKCommunity, **kwargs):
        super().__init__(**kwargs)
        self._community = community

    async def response(self) -> list:
        return await self._community.data()

    def size(self):
        return self._community.size

    @cache_method_ignore_args
    async def data(self) -> list[dict]:
        """
        Первый этап
        Сырые данные, просто словари, возвращаемые API, характеризующие пользователей
        """
        return await self._community.data()

    async def properties(self) -> dict:
        """
        Второй этап
        Один словарь по параметрам, названию свойства соответсвует Tied значение,
        то есть объект хранящий значение из оригинальных данных и id страницы где оно встречено
        """
        community = self._community
        params = {}

        data = await community.data()

        for item_name in vk_connections_names:
            params['connection_' + item_name] = get_field_values(data, item_name)

        params['sex'] = TiedCounter(get_field_values(data, 'sex'))
        params['city'] = TiedCounter(get_field_values(data, 'city', key='title'))
        params['country'] = TiedCounter(get_field_values(data, 'country', key='title'))
        params['online'] = TiedCounter(get_field_values(data, 'online'))
        params['online_mobile'] = TiedCounter(get_field_values(data, 'online_mobile'))
        params['verified'] = TiedCounter(get_field_values(data, 'verified', clean=True))
        params['home_town'] = TiedCounter(get_field_values(data, 'home_town', capitalize=True, clean=True))
        params['online_app'] = TiedCounter(get_field_values(data, 'online_app'))
        params['followers_count'] = sorted(get_field_values(data, 'followers_count'))
        last_seen = get_field_values(data, 'last_seen')
        params['last_seen_platform'] = TiedCounter(list_from_dicts(last_seen, 'platform'))
        params['last_seen_time'] = sorted(list_from_dicts(last_seen, 'time'))
        params['bdate'] = sorted([TiedValue(datetime.datetime.strptime(bdate.value, '%d.%m.%Y').timestamp(), bdate.id)
                                  for bdate in get_field_values(data, 'bdate') if
                                  len(bdate.value.split('.')) == 3])
        params['deactivated'] = TiedCounter(get_field_values(data, 'deactivated'))
        params['is_closed'] = TiedCounter(get_field_values(data, 'is_closed', clean=False))
        params['relation'] = TiedCounter(get_field_values(data, 'relation'))
        relatives_list = concatenate_lists(get_field_values(data, 'relatives'))
        params['relatives'] = TiedCounter(list_from_dicts(relatives_list, 'type'))
        personal_list = get_field_values(data, 'personal')
        params['personal_langs'] = TiedCounter(concatenate_lists(list_from_dicts(personal_list, 'langs')))
        params['personal_religion'] = TiedCounter(list_from_dicts(personal_list, 'religion', capitalize=True))
        for item in ['smoking', 'people_main', 'life_main', 'alcohol', 'political', 'inspired_by']:
            params['personal_' + item] = TiedCounter(list_from_dicts(personal_list, item, ignore_zero=True))

        occupation = sorted(get_field_values(data, 'occupation'), key=lambda x: x['type'].get_value())
        params['occupation_type'] = TiedCounter(list_from_dicts(occupation, 'type'))
        occupations_dict = {
            occupation_type: TiedCounter(list_from_dicts(occupations, 'name'))
            for occupation_type, occupations in groupby(occupation, lambda x: x['type'].get_value())
        }
        params['occupation'] = occupations_dict

        params['mobile_phone'] = get_field_values(data, 'mobile_phone', clean=True)
        params['home_phone'] = get_field_values(data, 'home_phone', clean=True)
        params['site'] = get_field_values(data, 'site', clean=True)
        params['status'] = get_field_values(data, 'status', clean=True)

        schools_list = TiedCounter(
            list_from_dicts(concatenate_lists(get_field_values(data, 'schools')), 'name'))
        params['school'] = schools_list

        universities_list = TiedCounter(
            list_from_dicts(concatenate_lists(get_field_values(data, 'universities')), 'name'))
        params['university'] = universities_list

        return params

    @cache_method_ignore_args
    async def processed(self):
        props = await self.properties()
        data = {
            'size': self._community.size
        }

        def time_delta(timestamp_list, dev=1):
            delta = [-(item - time()) / dev for item in timestamp_list]
            return delta

        all_ids_set = set(self._community.nodes)

        # groups = self.groups()
        # data['group'] = {
        #     'all_count': groups.size,
        #     'mean_count': groups.size / self.size,
        # }

        age = sorted(time_delta(props['bdate'], dev=31536000))

        data['age'] = {
            'count': len(age),
            **prepare_list([item for item in age if (item.value > 6) & (item.value < 80)], clean=True),
            'source_list': age
        }
        data['followers_count'] = {
            **prepare_list(props['followers_count'], clean=True, count=False),
            'source_list': props['followers_count']
        }
        data['city'] = {
            'count': props['city'].size,
            'source_list': props['city'].most_common(10, True)
        }
        data['country'] = {
            'count': props['country'].size,
            'source_list': props['country'].most_common(10, True)
        }
        data['is_closed'] = {
            'opened': props['is_closed'][0],
            'closed': props['is_closed'][1],
            'deleted': props['deactivated']['deleted'],
            'banned': props['deactivated']['banned'],
            'source_list': (props['is_closed'] + props['deactivated']).most_common()
        }

        common_towns = props['home_town'].most_common(8, True)
        data['home_town'] = {
            'count': props['home_town'].size,
            'source_list': common_towns,
        }
        last_seen = time_delta(props['last_seen_time'], dev=86400)
        data['last_seen_time'] = {
            **prepare_list(last_seen, count=False),
            'source_list': sorted(last_seen)
        }

        data['phone'] = {
            'mobile': get_tied_array_size(props['mobile_phone']),
            'home': get_tied_array_size(props['home_phone']),
        }
        data['status'] = {
            'count': get_tied_array_size(props['status'])
        }
        data['site'] = {
            'count': get_tied_array_size(props['site'])
        }

        data['last_seen_platform'] = {
            'source_list': props['last_seen_platform'].most_common()
        }

        # TODO Add apps properties (online, sources)
        data['online_mobile'] = {
            'count': props['online_mobile'],
        }
        # data['online'] = {
        #     'count': props['online']
        # }
        # occupation personal_inspired_by
        # ? personal_religion relation
        data['personal_religion'] = {
            'source_list': props['personal_religion'].most_common(),
            'count': props['personal_religion'].size
        }
        for item in ['langs', 'alcohol', 'life_main', 'people_main', 'political', 'smoking', 'inspired_by']:
            item_name = 'personal_' + item
            data[item_name] = {
                'source_list': props[item_name].most_common(),
                'count': props[item_name].size
            }

        data['relation'] = {
            'source_list': props['relation'].most_common()
        }
        data['relatives'] = {
            'source_list': props['relatives'].most_common()
        }
        data['sex'] = {
            'man': props['sex'][2],
            'woman': props['sex'][1],
            'source_list': props['sex'].most_common()
        }
        data['verified'] = {
            'count': props['verified'].size
        }
        data['occupation_type'] = {
            'source_list': props['occupation_type'].most_common(),
            'count': props['occupation_type'].size
        }
        data['occupation_school'] = {
            'source_list': props['occupation'].get('school', TiedCounter([])).most_common(),
            'count': props['occupation'].get('school', TiedCounter([])).size
        }
        data['occupation_work'] = {
            'source_list': props['occupation'].get('work', TiedCounter([])).most_common(),
            'count': props['occupation'].get('work', TiedCounter([])).size
        }
        data['occupation_university'] = {
            'source_list': props['occupation'].get('university', TiedCounter([])).most_common(),
            'count': props['occupation'].get('university', TiedCounter([])).size
        }

        data['school'] = {
            'count': props['school'].size,
            'source_list': props['school'].most_common(ignore_single=True)
        }
        data['university'] = {
            'count': props['school'].size,
            'source_list': props['university'].most_common(ignore_single=True)
        }

        return data

    async def all(self):
        data = await self.processed()

        properties = [
            self._gen_property_category(data,
                                        'age', 'Возраст',
                                        [
                                            ('commonMean', 'Наисреднейший'),
                                        ],
                                        PlotType.LINE
                                        ),
            self._gen_property_category(data,
                                        'sex', 'Пол',
                                        [
                                            ('man', 'Мужской'),
                                            ('woman', 'Женский'),
                                        ],
                                        PlotType.CIRCULAR,
                                        self._gen_circular_plot(data['sex']['source_list'],
                                                                name=lambda
                                                                    value: 'Мужской' if value.get_value() == 2 else 'Женский',
                                                                color=lambda
                                                                    value: '#989FFF' if value.get_value() == 2 else '#FD8DA6')
                                        ),
            self._gen_property_category(data, 'city', 'Город', [], PlotType.CIRCULAR, common_count=3),
            # self._gen_property_category(data, 'group', 'Группы', [
            #     ('all_count', 'Уникальных групп'),
            #     ('mean_count', 'На человека')], None),
            self._gen_property_category(data, 'school', 'Школа', [], PlotType.CIRCULAR, common_count=5),
            self._gen_property_category(data, 'university', 'Университет (архив)', [], PlotType.CIRCULAR,
                                        common_count=5),
            self._gen_property_category(data, 'verified', 'Верификация', [('count', 'Количество')], None),
            self._gen_property_category(data, 'status', 'Статус', [], None),
            self._gen_property_category(data, 'site', 'Сайт', [], None),
            self._gen_property_category(data, 'phone', 'Телефон', [('mobile', 'Мобильный'), ('home', 'Домашний')],
                                        None),
            self._gen_property_category(data, 'country', 'Страна', [], PlotType.CIRCULAR, common_count=3),
            self._gen_property_category(data, 'relatives', 'Среди родственников есть', [], PlotType.CIRCULAR,
                                        name_func=lambda x: relatives_dict[x],
                                        common_count=3),
            self._gen_property_category(data, 'occupation_type', 'Род занятий', [], PlotType.CIRCULAR,
                                        name_func=lambda x: occupation_type_dict[x],
                                        common_count=3),
            self._gen_property_category(data, 'occupation_work', 'Работа', [], PlotType.CIRCULAR, common_count=3),
            self._gen_property_category(data, 'occupation_school', 'Текущая школа', [], PlotType.CIRCULAR,
                                        common_count=3),
            self._gen_property_category(data, 'occupation_university', 'Университет', [], PlotType.CIRCULAR,
                                        common_count=3),
            self._gen_property_category(data, 'personal_political', 'Политические предпочтения', [], PlotType.CIRCULAR,
                                        name_func=lambda x: political_dict.get(x),
                                        common_count=3),
            self._gen_property_category(data, 'personal_people_main', 'Главное в людях', [], PlotType.CIRCULAR,
                                        name_func=lambda x: people_main_dict[x],
                                        common_count=3),
            self._gen_property_category(data, 'personal_life_main', 'Главное в жизни', [], PlotType.CIRCULAR,
                                        name_func=lambda x: life_main_dict[x],
                                        common_count=3),
            self._gen_property_category(data, 'personal_smoking', 'Отношение к курению', [], PlotType.CIRCULAR,
                                        name_func=lambda x: smoking_dict[x],
                                        common_count=3),
            self._gen_property_category(data, 'personal_alcohol', 'Отношение к алкоголю', [], PlotType.CIRCULAR,
                                        name_func=lambda x: alcohol_dict[x],
                                        common_count=3),
            self._gen_property_category(data, 'relation', 'Семейное положение', [], PlotType.CIRCULAR,
                                        name_func=lambda x: relation_dict[x],
                                        common_count=5),
            self._gen_property_category(data, 'last_seen_time', 'Время последнего посещения (в днях)', [
                ('mean', 'Среднее'),
                ('max', 'Максимальное'),
                ('min', 'Минимальное'),
                ('median', 'Медианное'),
            ], PlotType.LINE),
            self._gen_property_category(data, 'home_town', 'Родной город', [], PlotType.CIRCULAR, common_count=3),
            self._gen_property_category(data,
                                        'is_closed', 'Статус аккаунта',
                                        [
                                            ('opened', 'Открытый'),
                                            ('closed', 'Приватный'),
                                            ('banned', 'Забаненный'),
                                            ('deleted', 'Удаленный'),
                                        ],
                                        PlotType.CIRCULAR,
                                        self._gen_circular_plot(data['is_closed']['source_list'],
                                                                name=lambda
                                                                    x: account_status_dict.get(x, ['Неизвестный тип'])[
                                                                    0],
                                                                color=lambda x: account_status_dict.get(x, ['#ffffff'])[
                                                                    1])),
            # self._gen_property_category(data, 'online', 'Онлайн', [], PlotType.CIRCULAR, common_count=5),
            self._gen_property_category(data, 'personal_langs', 'Языки', [], PlotType.CIRCULAR, common_count=5),
            self._gen_property_category(data, 'personal_religion', 'Мировоззрение', [], PlotType.CIRCULAR,
                                        common_count=5),
            self._gen_property_category(data, 'last_seen_platform', 'Последнее посещение', [], PlotType.CIRCULAR,
                                        common_count=5,
                                        name_func=lambda x: last_seen_platform_dict[x]),
            self._gen_property_category(data, 'followers_count', 'Количество подписчиков',
                                        [
                                            ('max', 'Максимальное'),
                                            ('min', 'Минимальное'),
                                            ('mean', 'Среднее'),
                                            ('median', 'Медианное'),
                                        ], PlotType.LINE),
        ]
        return bool_filter(properties)

    async def interesting(self):
        all_props = await self.all()

        # processed_data = self.process_data()

        def importance_metrics(prop):
            name = prop['name']
            prop_id = prop['id']
            category = prop_id.split('.')[1]
            prop_name = prop_id.split('.')[2]
            value_dict = prop['value']
            value = value_dict['value']
            value_type = value_dict['type']
            percent = value_dict.get('percent', 0)
            metric = 0
            categories = {
                'school': {'min_percent': 10, 'importance': 7},
                'sex': {'min_percent': 50, 'importance': 3},
                'city': {'min_percent': 30, 'importance': 4},
                'country': {'min_percent': 70, 'importance': 2},
                'occupation_university': {'min_percent': 20, 'importance': 7},
                'university': {'min_percent': 20, 'importance': 6},
                'verified': {'min_percent': 5, 'importance': 18},
            }
            if category in categories:
                prop_data = categories[category]
                min_percent = prop_data['min_percent']

                if percent >= min_percent:
                    metric = (percent - min_percent) / min_percent * prop_data['importance']

                if prop_name == 'count':
                    metric /= 10
                # if prop_name != 'count':
                #     metric *= prop_data['importance']
                # else:
                #     metric /= 10

            return metric

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
        ]), key=lambda prop: importance_metrics(prop), reverse=True)

    async def features(self):
        community = self._community
        if not community.nodes:
            return {}

        data = await self.processed()
        assert isinstance(data, dict)

        features = self._common_features(
            data,
            category_frequency_features={
                'relation', 'sex', 'personal.life_main', 'personal.langs',
                'personal.religion', 'personal.people_main',
                'personal.political', 'relatives',
                'personal.smoking', 'personal.alcohol'
            }, plain_features={
                'status.len_median',
            }, frequency_features={
                'site.site_good_count',
                'site.good_count',
                'site.status_count',
                'site.site_count'
            }
        )
        assert isinstance(features, dict)

        size = self._community.size

        for feature in ['personal.smoking', 'personal.alcohol']:
            feature_common_list = get_value_by_path(data, feature)
            if feature_common_list:
                sum_count = sum(map(lambda x: x[1], feature_common_list))
                features[feature] = \
                    sum(map(lambda x: x[0] * x[1], feature_common_list)) / sum_count
                features[feature + '_count'] = sum_count / size

        for username, value in data['username'].items():
            features[f'username.{username}'] = value['count'] / size

        for i, university in enumerate(data['university'][:2]):
            features[f'university-{i}'] = university['count'] / size

        for i, school in enumerate(data['school'][:2]):
            features[f'school-{i}'] = school['count'] / size

        features = {key: value for key, value in features.items() if not np.isnan(value)}
        return features

    @classmethod
    def _prepare_username_list(cls, username_list, service_name):
        usernames = []
        if service_name in ['vk', 'instagram', 'facebook', 'twitter']:
            for url in username_list:
                url = url.strip('/ ')
                site_items = url.split('/')
                if len(site_items) > 1 and is_good_username(site_items[-1]):
                    usernames.append(site_items[-1])
                elif len(site_items) == 1 and is_good_username(site_items[0]):
                    usernames.append(site_items[0])
        elif service_name in ['livejournal']:
            for url in username_list:
                url = url.strip('/ ')
                url = url.split('//')[-1]
                site_items = url.split('.')
                if len(site_items) == 3 and is_good_username(site_items[0]):
                    usernames.append(site_items[0])
                elif len(site_items) == 1 and is_good_username(site_items[0]):
                    usernames.append(site_items[0])

        elif service_name in ['skype']:
            for username in username_list:
                if is_good_username(username):
                    usernames.append(username)
        return clear_list(usernames)

    def _gen_property_category(self, data, key, name, props,
                               plot_type=None, plot_data=None, common_count=0, name_func=None, names_dict=None):
        if names_dict:
            name_func = lambda x: names_dict.get(x, 'Идентификатор не найден')

        if data[key].get('count', 1) == 0:
            return None
        sup_properties = []

        if common_count:
            source_list = data[key]['source_list']
            for idx in range(common_count):
                if len(source_list) > idx:
                    sub_prop_name = source_list[idx][0].value
                    if name_func:
                        sub_prop_name = name_func(sub_prop_name)
                    sup_properties.append(self._gen_prop(f'top_{idx}', sub_prop_name, source_list[idx][1],
                                                         source_list[idx][0].get_ids()))
        added_sub_keys = set()
        for sub_property in props:
            sub_key = sub_property[0]
            if sub_key in data[key] and sub_key not in added_sub_keys:
                added_sub_keys.add(sub_key)
                sub_name = sub_property[1]
                sub_value = data[key][sub_key]
                sup_properties.append(self._gen_prop(sub_key, sub_name, sub_value))

        values = bool_filter(sup_properties)
        if not values:
            return None
        return {
            'name': name,
            'values': values
        }

    @classmethod
    def _gen_circular_plot(cls, items, name=None, color=None):
        if color is None:
            color = lambda x: get_random_color()
        if name is None:
            name = lambda value: value.get_value()
        return [
            {
                'value': count,
                'name': name(value),
                'color': color(value)
            }
            for value, count in items if count > 0
        ]

    def _gen_prop(self, id_, name_, value_, ids=None):
        value_dict = {}
        if isinstance(value_, TiedValue):
            value_, ids = value_.get_value(), value_.get_ids()

        try:
            value_ = float(value_)
        except:
            pass

        if isinstance(value_, float):
            value_dict['value'] = round(value_, 2)
            value_dict['type'] = 'num'
        elif isinstance(value_, str):
            value_dict['value'] = value_
            value_dict['type'] = 'str'
        else:
            logger.warning('Unknown property value type %s %s', type(value_), value_)
            return None

        if ids and len(ids) > 1:
            value_dict['percent'] = round(len(ids) / self._community.size * 100, 2)

        if not value_ or (isinstance(value_, float) and np.isnan(value_)):
            return None
        return {
            'id': id_,
            'name': name_.capitalize(),
            'value': value_dict,
        }

    @classmethod
    def _common_features(cls, data, category_frequency_features=None,
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
            features[feature] = get_value_by_path(data, feature)
        for feature in frequency_features:
            features[feature] = get_value_by_path(data, feature) / size

        for feature in category_frequency_features:
            for key, value in get_value_by_path(data, feature):
                if isinstance(key, str):
                    key = re.sub('[^а-яa-z0-9]', ' ', key.lower())
                    key = '_'.join(key.split())
                else:
                    assert isinstance(key, int)
                features[f'{feature}-{key}'] = value / size

        features = {key: value for key, value in features.items() if not np.isnan(value)}
        return features

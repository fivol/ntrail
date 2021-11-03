import re

from server.helpers.tied_value import TiedValue
from pycommon.decors import cache_method
from server.helpers.types import PlotType
from server.plugin.plugin import BasePlugin
from core import VKCommunity


class VKCommunityPlugin(BasePlugin):
    name = 'community'
    _proxy_attributes = ['name', 'size']

    def __init__(self, community: VKCommunity, **kwargs):
        super().__init__(**kwargs)
        self._community = community

    def size(self):
        return self._community.size

    def summery(self):
        return {
            'name': self._community.name,
            'size': self._community.size
        }

    def response(self) -> dict:
        return self._community.data()


class VKCommunityPropsPlugin(BasePlugin):
    name = 'community-props'

    def __init__(self, community: VKCommunity, **kwargs):
        super().__init__(**kwargs)
        self._community = community

    @cache_method
    def process_data(self):
        props = self.properties()
        data = {
            'size': self.size
        }

        def time_delta(timestamp_list, dev=1):
            delta = [-(item - time()) / dev for item in timestamp_list]
            return delta

        def prepare_username_list(username_list, service_name):
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

        all_ids_set = set(self._community.ids)

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

        common_apps = props['online_app'].most_common()
        VKAPI.get_apps_data([item[0].get_value() for item in common_apps])
        apps_list = [(value.with_value(VKAPI.get_apps_data([value.get_value()])[0]['title']), count)
                     for value, count in common_apps]

        mobile_ids_set = set(props['online_mobile'][1].get_ids())
        mobile_other = list(mobile_ids_set - set(sum([item[0].get_ids() for item in apps_list], [])))
        online_mobile = (TiedValue('С мобилы (другое)', mobile_other), len(mobile_other))
        online_ids_set = set(props['online'][1].get_ids())
        online_other_ids = list(online_ids_set - mobile_ids_set)
        online_other = (TiedValue('С компа', online_other_ids), len(online_other_ids))
        not_online_ids = list(all_ids_set - online_ids_set)
        not_online = (TiedValue('Оффлайн', not_online_ids), len(not_online_ids))

        apps_list.append(online_mobile)
        apps_list.append(online_other)
        apps_list.append(not_online)
        data['online'] = {
            'source_list': sorted(apps_list, key=lambda x: x[1], reverse=True)
        }
        data['online_mobile'] = {
            'count': props['online_mobile'],
        }
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

    def important(self):
        return [
            {
                'id': 0,
                'name': 'Количество',
                'value': self.size
            },
            {
                'id': 2,
                'name': 'Тип кластера',
                'value': 'Пользователи VK'
            }
        ]

    def all(self):
        data = self.process_data()

        properties = [
            self.gen_property_category(
                'age', 'Возраст',
                [
                    ('commonMean', 'Наисреднейший'),
                ],
                PlotType.LINE
            ),
            self.gen_property_category(
                'sex', 'Пол',
                [
                    ('man', 'Мужской'),
                    ('woman', 'Женский'),
                ],
                PlotType.CIRCULAR,
                self.gen_circular_plot(data['sex']['source_list'],
                                       name=lambda value: 'Мужской' if value.get_value() == 2 else 'Женский',
                                       color=lambda value: '#989FFF' if value.get_value() == 2 else '#FD8DA6')
            ),
            self.gen_property_category('city', 'Город', [], PlotType.CIRCULAR, common_count=3),
            # self.gen_property_category('group', 'Группы', [
            #     ('all_count', 'Уникальных групп'),
            #     ('mean_count', 'На человека')], None),
            self.gen_property_category('school', 'Школа', [], PlotType.CIRCULAR, common_count=5),
            self.gen_property_category('university', 'Университет (архив)', [], PlotType.CIRCULAR, common_count=5),
            self.gen_property_category('verified', 'Верификация', [('count', 'Количество')], None),
            self.gen_property_category('status', 'Статус', [], None),
            self.gen_property_category('site', 'Сайт', [], None),
            self.gen_property_category('phone', 'Телефон', [('mobile', 'Мобильный'), ('home', 'Домашний')], None),
            self.gen_property_category('country', 'Страна', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category('relatives', 'Среди родственников есть', [], PlotType.CIRCULAR,
                                       name_func=lambda x: relatives_dict[x],
                                       common_count=3),
            self.gen_property_category('occupation_type', 'Род занятий', [], PlotType.CIRCULAR,
                                       name_func=lambda x: occupation_type_dict[x],
                                       common_count=3),
            self.gen_property_category('occupation_work', 'Работа', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category('occupation_school', 'Текущая школа', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category('occupation_university', 'Университет', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category('personal_political', 'Политические предпочтения', [], PlotType.CIRCULAR,
                                       name_func=lambda x: political_dict.get(x),
                                       common_count=3),
            self.gen_property_category('personal_people_main', 'Главное в людях', [], PlotType.CIRCULAR,
                                       name_func=lambda x: people_main_dict[x],
                                       common_count=3),
            self.gen_property_category('personal_life_main', 'Главное в жизни', [], PlotType.CIRCULAR,
                                       name_func=lambda x: life_main_dict[x],
                                       common_count=3),
            self.gen_property_category('personal_smoking', 'Отношение к курению', [], PlotType.CIRCULAR,
                                       name_func=lambda x: smoking_dict[x],
                                       common_count=3),
            self.gen_property_category('personal_alcohol', 'Отношение к алкоголю', [], PlotType.CIRCULAR,
                                       name_func=lambda x: alcohol_dict[x],
                                       common_count=3),
            self.gen_property_category('relation', 'Семейное положение', [], PlotType.CIRCULAR,
                                       name_func=lambda x: relation_dict[x],
                                       common_count=5),
            self.gen_property_category('last_seen_time', 'Время последнего посещения (в днях)', [
                ('mean', 'Среднее'),
                ('max', 'Максимальное'),
                ('min', 'Минимальное'),
                ('median', 'Медианное'),
            ], PlotType.LINE),
            self.gen_property_category('home_town', 'Родной город', [], PlotType.CIRCULAR, common_count=3),
            self.gen_property_category(
                'is_closed', 'Статус аккаунта',
                [
                    ('opened', 'Открытый'),
                    ('closed', 'Приватный'),
                    ('banned', 'Забаненный'),
                    ('deleted', 'Удаленный'),
                ],
                PlotType.CIRCULAR,
                self.gen_circular_plot(data['is_closed']['source_list'],
                                       name=lambda
                                           x: account_status_dict.get(x, ['Неизвестный тип'])[0],
                                       color=lambda x: account_status_dict.get(x, ['#ffffff'])[1])),
            self.gen_property_category('online', 'Онлайн', [], PlotType.CIRCULAR, common_count=5),
            self.gen_property_category('personal_langs', 'Языки', [], PlotType.CIRCULAR, common_count=5),
            self.gen_property_category('personal_religion', 'Мировоззрение', [], PlotType.CIRCULAR, common_count=5),
            self.gen_property_category('last_seen_platform', 'Последнее посещение', [], PlotType.CIRCULAR,
                                       common_count=5,
                                       name_func=lambda x: last_seen_platform_dict[x]),
            self.gen_property_category('followers_count', 'Количество подписчиков',
                                       [
                                           ('max', 'Максимальное'),
                                           ('min', 'Минимальное'),
                                           ('mean', 'Среднее'),
                                           ('median', 'Медианное'),
                                       ], PlotType.LINE),
        ]
        return bool_filter(properties)

    def get_interesting_properties(self):
        all_props = self.all()

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

        base_id = self.hash
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

    def properties(self):
        params = {}

        data = self.data()

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

    def features(self):
        if not self.ids:
            return {}

        data = self.process_data()
        assert isinstance(data, dict)

        features = self.get_common_features(
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

        size = self.size

        for feature in ['personal.smoking', 'personal.alcohol']:
            feature_common_list = self.get_value_by_path(data, feature)
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

    def response(self) -> dict:
        return self.all()


class ExpandCommunityPlugin(BasePlugin):
    def __init__(self, community: VKCommunity):
        self._community = community

    @classmethod
    def expand(cls, nodes_part, weight_reduction_ratio=0.95, break_point=10, max_nodes=300):
        community = set(nodes_part)
        VkMethods.friends.sync_map(community)
        friends_counter = collections.Counter(
            sum([list(set(VkMethods.friends.sync(user)) - set(community)) for user in community], []))
        community_friends_amount_changes = []
        max_iterations = max_nodes
        count = 0
        curr_weight = 1
        while friends_counter.most_common(1)[0][1] > break_point and max_iterations > 0:
            count += 1
            curr_weight *= weight_reduction_ratio
            max_iterations -= 1
            new_participant, community_friends_amount = friends_counter.most_common(1)[0]
            community_friends_amount_changes.append(community_friends_amount)
            community.add(new_participant)
            del friends_counter[new_participant]
            unique_friends = set(VkMethods.friends.sync(new_participant)) - set(community)
            new_participant_unique_friends = collections.Counter(
                dict(
                    zip(
                        unique_friends,
                        [curr_weight] * len(unique_friends)
                    )

                )
            )
            friends_counter += new_participant_unique_friends
        return cls(community)

    def response(self) -> dict:
        return {}

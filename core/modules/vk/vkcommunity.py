# информация о полях из раздела «Жизненная позиция».
# political (integer) — политические предпочтения. Возможные значения:
# 1 — коммунистические;
# 2 — социалистические;
# 3 — умеренные;
# 4 — либеральные;
# 5 — консервативные;
# 6 — монархические;
# 7 — ультраконсервативные;
# 8 — индифферентные;
# 9 — либертарианские.
# langs (array) — языки.
# religion (string) — мировоззрение.
# inspired_by (string) — источники вдохновения.
# people_main (integer) — главное в людях. Возможные значения:
# 1 — ум и креативность;
# 2 — доброта и честность;
# 3 — красота и здоровье;
# 4 — власть и богатство;
# 5 — смелость и упорство;
# 6 — юмор и жизнелюбие.
# life_main (integer) — главное в жизни. Возможные значения:
# 1 — семья и дети;
# 2 — карьера и деньги;
# 3 — развлечения и отдых;
# 4 — наука и исследования;
# 5 — совершенствование мира;
# 6 — саморазвитие;
# 7 — красота и искусство;
# 8 — слава и влияние;
# smoking (integer) — отношение к курению. Возможные значения:
# 1 — резко негативное;
# 2 — негативное;
# 3 — компромиссное;
# 4 — нейтральное;
# 5 — положительное.
# alcohol (integer) — отношение к алкоголю. Возможные значения:
# 1 — резко негативное;
# 2 — негативное;
# 3 — компромиссное;
# 4 — нейтральное;
# 5 — положительное.
import random
from more_itertools import unique_everseen

from .vkgroup import VKGroup
from .vkgroups import VKGroups
from core.module.represent import try_base_analog, Represent
from core.module.represent_tools import RepresentTools
from core.module.tied_counter import TiedCounter
from core.module.tied_value import TiedValue, get_tied_array_size
from core.tools import once_property, name_to_gent, concatenate_lists, \
    bool_filter, merge_lists, get_field_values
from core.tools import cache_method
import numpy as np
import networkx as nx
import collections
from collections import Counter
import datetime
from time import time
from .vkuser import VKUser
import math
from itertools import groupby
from core.tools import clear_list, prepare_list, list_from_dicts, is_good_username
import re
from .vkapi import VKAPI
from core.constants import PLOT_LINE, PLOT_CIRCULAR

# @ - полное говнище, но надо куда нибудь прикрутить
# # - параметр обработан
# ! - доработать параметр


# '@photo_200', '@about', '@activities', '#bdate', '@books', '@career', '#city', '@connections',
# '#sex', '@contacts', '#country', '@education', '@exports', '#followers_count', '#home_town', '@interests',
# '#last_seen', '@maiden_name', '@military', '@movies', '@music', '@nickname', '!occupation', '#online',
# '#personal', '@quotes', '#relatives', '#relation', '!schools', '#site', '#status', '#trending', '#tv',
# '!universities', '#verified', '#counters'
# sex 2-man 1-woman

vk_connections_names = ['skype', 'livejournal', 'instagram', 'facebook', 'twitter']

account_status_dict = {
    0: ('Открытый', '#00682E'),
    1: ('Приватный', '#8D1E00'),
    'deleted': ('Удаленный', '#000000'),
    'banned': ('Забаненный', '#530742'),
}
relation_dict = {
    1: 'Не женат',
    2: 'Есть друг',
    3: 'Помолвлен',
    4: 'Женат',
    5: 'Всё сложно',
    6: 'В активном поиске',
    7: 'Влюблён',
    8: 'В гражданском браке',
    0: 'Не указано',
}
relatives_dict = {
    'child': 'Сын / Дочь',
    'sibling': 'Брат / Сестра',
    'parent': 'Отец / Мать',
    'grandparent': 'Дедушка / Бабушка',
    'grandchild': 'Внук / Внучка',
}
last_seen_platform_dict = {
    1: 'Мобильная версия',
    2: 'iPhone',
    3: 'iPad',
    4: 'Android',
    5: 'Windows Phone',
    6: 'Windows 10',
    7: 'Сайт',
}
political_dict = {
    1: 'Коммунистические',
    2: 'Социалистические',
    3: 'Умеренные',
    4: 'Либеральные',
    5: 'Консервативные',
    6: 'Монархические',
    7: 'Ультраконсервативные',
    8: 'Индифферентные',
    9: 'Либертарианские',
}
people_main_dict = {
    1: 'Ум и креативность',
    2: 'Доброта и честность',
    3: 'Красота и здоровье',
    4: 'Власть и богатство',
    5: 'Смелость и упорство',
    6: 'Юмор и жизнелюбие',
}
life_main_dict = {
    1: 'Семья и дети',
    2: 'Карьера и деньги',
    3: 'Развлечения и отдых',
    4: 'Наука и исследования',
    5: 'Совершенствование мира',
    6: 'Саморазвитие',
    7: 'Красота и искусство',
    8: 'Слава и влияние',
}
smoking_dict = {
    1: 'Резко негативное',
    2: 'Негативное',
    3: 'Компромиссное',
    4: 'Нейтральное',
    5: 'Положительное',
}
alcohol_dict = {
    1: 'Резко негативное',
    2: 'Негативное',
    3: 'Компромиссное',
    4: 'Нейтральное',
    5: 'Положительное',
}
occupation_type_dict = {
    'work': 'Текущая работа',
    'school': 'Текущая школа',
    'university': 'Текущий университет'
}


class VKCommunity(Represent, VKAPI, RepresentTools):
    base_class = VKUser
    available_attributes = ['friends', 'clusters', 'groups']

    def __init__(self, users=None, main=None, clear=False, save_features=False, target=None, target_value=None, **kwargs):
        super().__init__()
        self.target_value = target_value
        if isinstance(users, set):
            users = list(users)
        assert main is None or isinstance(main, VKUser) or isinstance(main, VKGroup), main
        self.main = main
        self.nodes = []
        self.counter = Counter()
        self.target = target

        if isinstance(users, Counter):
            self.counter = users
            self.nodes = [i[0] for i in self.counter.most_common()]
        elif isinstance(users, list):
            users = list(filter(lambda x: x is not None, unique_everseen(users)))
            if users:
                if isinstance(users[0], VKUser):
                    self.nodes = [user.id for user in users]
                elif isinstance(users[0], int):
                    self.nodes = users
                elif isinstance(users[0], str):
                    id_ = VKUser.parse_id(users[0])
                    if id_:
                        self.nodes = [VKUser.parse_id(id_) for id_ in users]
                    else:
                        usernames = [VKUser.extract_username(url) for url in users]
                        usernames = clear_list(usernames)
                        self.resolve_screen_names(usernames)
                        self.nodes = [VKUser(username).id for username in usernames]
                        self.nodes = clear_list(self.nodes)
                else:
                    raise TypeError('user instance must be int or string, but' + str(type(users[0])))
            self.counter = Counter(self.nodes)
        elif isinstance(users, str):
            usernames = VKCommunity.parse_usernames(users)
            self.resolve_screen_names(usernames)
            self.nodes = [VKUser(username).id for username in usernames]
            self.nodes = clear_list(self.nodes)
            self.counter = Counter(self.nodes)
        elif not (users is None):
            raise TypeError('Wrong users type: {}'.format(type(users)))
        if 3 < self.size < 800 and save_features:
            self.save_features()

    @staticmethod
    def parse_usernames(usernames_string):
        usernames = re.findall(r'vk.com/([0-9a-z._]+)', usernames_string)
        return list(set(usernames))

    def get_deactivated(self):
        self.data_dict()
        return VKCommunity([user for user in self.objects if not user.valid], clear=False)

    def all_groups(self):
        all_groups_ids = sum(
            filter(
                lambda x: isinstance(x, list), self.get_users_groups(self.nodes)),
            [])
        return VKGroups(all_groups_ids)

    @try_base_analog
    def groups(self):
        all_groups = sum(
            filter(
                lambda x: isinstance(x, list), self.get_users_groups(self.nodes)),
            [])

        counter = Counter(all_groups)
        groups = VKGroups(counter).select()
        groups_order = groups.order()
        top_groups = groups_order.select(50)
        return top_groups

    def short_info(self):
        return ''

    @cache_method
    def data_list(self, force=False):
        return self.get_users(self.nodes, full=True, force=force)

    @try_base_analog
    def friends(self):
        users_friends = self.get_users_friends(self.nodes)
        return VKCommunity(sum(filter(lambda x: isinstance(x, list), users_friends), []))

    def get_connections(self):
        connections = self.get_users_friends(self.nodes)
        return {
            first_id: [second_id for second_id in connected_list if second_id in self.nodes]
            for (first_id, connected_list) in zip(self.nodes, connections)
        }

    def only_valid(self):
        self.preload()
        return VKCommunity(
            Counter({user.id: self.counter[user.id] for user in self.objects if user.valid}),
            clear=False
        )

    @classmethod
    def generate_random(cls, size):
        comm = VKCommunity()
        while comm.size < size:
            min_vkid = 1
            max_vkid = 420000000
            ids_list = random.sample(range(min_vkid, max_vkid), size * 2)
            comm = VKCommunity(list(ids_list)).only_valid().select(size)
        return comm

    def connectedness(self):
        trs = nx.triangles(self.graph)
        ratio = math.log(1 + sum(trs.values()) / self.size)
        return ratio

    @classmethod
    def expand(cls, nodes_part, weight_reduction_ratio=0.95, break_point=10, max_nodes=300):
        community = set(nodes_part)
        cls.get_users_friends(community)
        friends_counter = collections.Counter(
            sum([list(set(cls.get_user_friends(user)) - set(community)) for user in community], []))
        # bapi.get_users_friends([i[0] for i in friends_counter.most_common(75)])
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
            unique_friends = set(cls.get_user_friends(new_participant)) - set(community)
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

    def get_features(self):
        if not self.nodes:
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

    def get_ids(self):
        return [VKUser.gen_id(id_) for id_ in self.nodes]

    @once_property
    def params(self):
        params = {}

        data_list = self.data_list()

        def true_date(date_str):
            try:
                datetime.datetime.strptime(date_str, '%d.%m.%Y')
                return True
            except ValueError:
                return False

        for item_name in vk_connections_names:
            params['connection_' + item_name] = get_field_values(data_list, item_name)

        params['sex'] = TiedCounter(get_field_values(data_list, 'sex'))
        params['city'] = TiedCounter(get_field_values(data_list, 'city', key='title'))
        params['country'] = TiedCounter(get_field_values(data_list, 'country', key='title'))
        params['online'] = TiedCounter(get_field_values(data_list, 'online'))
        params['online_mobile'] = TiedCounter(get_field_values(data_list, 'online_mobile'))
        params['verified'] = TiedCounter(get_field_values(data_list, 'verified', clean=True))
        params['home_town'] = TiedCounter(get_field_values(data_list, 'home_town', capitalize=True, clean=True))
        params['online_app'] = TiedCounter(get_field_values(data_list, 'online_app'))
        params['followers_count'] = sorted(get_field_values(data_list, 'followers_count'))
        last_seen = get_field_values(data_list, 'last_seen')
        params['last_seen_platform'] = TiedCounter(list_from_dicts(last_seen, 'platform'))
        params['last_seen_time'] = sorted(list_from_dicts(last_seen, 'time'))
        params['bdate'] = sorted([TiedValue(datetime.datetime.strptime(bdate.value, '%d.%m.%Y').timestamp(), bdate.id)
                                  for bdate in get_field_values(data_list, 'bdate') if
                                  len(bdate.value.split('.')) == 3])
        params['deactivated'] = TiedCounter(get_field_values(data_list, 'deactivated'))
        params['is_closed'] = TiedCounter(get_field_values(data_list, 'is_closed', clean=False))
        params['relation'] = TiedCounter(get_field_values(data_list, 'relation'))
        relatives_list = concatenate_lists(get_field_values(data_list, 'relatives'))
        params['relatives'] = TiedCounter(list_from_dicts(relatives_list, 'type'))
        personal_list = get_field_values(data_list, 'personal')
        params['personal_langs'] = TiedCounter(concatenate_lists(list_from_dicts(personal_list, 'langs')))
        params['personal_religion'] = TiedCounter(list_from_dicts(personal_list, 'religion', capitalize=True))
        for item in ['smoking', 'people_main', 'life_main', 'alcohol', 'political', 'inspired_by']:
            params['personal_' + item] = TiedCounter(list_from_dicts(personal_list, item, ignore_zero=True))

        occupation = sorted(get_field_values(data_list, 'occupation'), key=lambda x: x['type'].get_value())
        params['occupation_type'] = TiedCounter(list_from_dicts(occupation, 'type'))
        occupations_dict = {
            occupation_type: TiedCounter(list_from_dicts(occupations, 'name'))
            for occupation_type, occupations in groupby(occupation, lambda x: x['type'].get_value())
        }
        params['occupation'] = occupations_dict

        params['mobile_phone'] = get_field_values(data_list, 'mobile_phone', clean=True)
        params['home_phone'] = get_field_values(data_list, 'home_phone', clean=True)
        params['site'] = get_field_values(data_list, 'site', clean=True)
        params['status'] = get_field_values(data_list, 'status', clean=True)

        schools_list = TiedCounter(
            list_from_dicts(concatenate_lists(get_field_values(data_list, 'schools')), 'name'))
        params['school'] = schools_list

        universities_list = TiedCounter(
            list_from_dicts(concatenate_lists(get_field_values(data_list, 'universities')), 'name'))
        params['university'] = universities_list

        return params

    @classmethod
    def search_query(cls, search_str):
        return VKCommunity(
            list(map(lambda x: x['profile']['id'],
                     filter(lambda x: x['type'] == 'profile',
                            cls.search(search_str, limit=20)['items']))),
            target='search',
            target_value=search_str
        )

    @cache_method
    def process_data(self):
        params = self.params
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

        all_ids_set = set(self.nodes)

        # groups = self.groups()
        # data['group'] = {
        #     'all_count': groups.size,
        #     'mean_count': groups.size / self.size,
        # }

        age = sorted(time_delta(params['bdate'], dev=31536000))

        data['age'] = {
            'count': len(age),
            **prepare_list([item for item in age if (item.value > 6) & (item.value < 80)], clean=True),
            'source_list': age
        }
        data['followers_count'] = {
            **prepare_list(params['followers_count'], clean=True, count=False),
            'source_list': params['followers_count']
        }
        data['city'] = {
            'count': params['city'].size,
            'source_list': params['city'].most_common(10, True)
        }
        data['country'] = {
            'count': params['country'].size,
            'source_list': params['country'].most_common(10, True)
        }
        data['is_closed'] = {
            'opened': params['is_closed'][0],
            'closed': params['is_closed'][1],
            'deleted': params['deactivated']['deleted'],
            'banned': params['deactivated']['banned'],
            'source_list': (params['is_closed'] + params['deactivated']).most_common()
        }

        common_towns = params['home_town'].most_common(8, True)
        data['home_town'] = {
            'count': params['home_town'].size,
            'source_list': common_towns,
        }
        last_seen = time_delta(params['last_seen_time'], dev=86400)
        data['last_seen_time'] = {
            **prepare_list(last_seen, count=False),
            'source_list': sorted(last_seen)
        }

        data['phone'] = {
            'mobile': get_tied_array_size(params['mobile_phone']),
            'home': get_tied_array_size(params['home_phone']),
        }
        data['status'] = {
            'count': get_tied_array_size(params['status'])
        }
        data['site'] = {
            'count': get_tied_array_size(params['site'])
        }

        data['last_seen_platform'] = {
            'source_list': params['last_seen_platform'].most_common()
        }

        common_apps = params['online_app'].most_common()
        VKAPI.get_apps_data([item[0].get_value() for item in common_apps])
        apps_list = [(value.with_value(VKAPI.get_apps_data([value.get_value()])[0]['title']), count)
                     for value, count in common_apps]

        mobile_ids_set = set(params['online_mobile'][1].get_ids())
        mobile_other = list(mobile_ids_set - set(sum([item[0].get_ids() for item in apps_list], [])))
        online_mobile = (TiedValue('С мобилы (другое)', mobile_other), len(mobile_other))
        online_ids_set = set(params['online'][1].get_ids())
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
            'count': params['online_mobile'],
        }
        # occupation personal_inspired_by
        # ? personal_religion relation
        data['personal_religion'] = {
            'source_list': params['personal_religion'].most_common(),
            'count': params['personal_religion'].size
        }
        for item in ['langs', 'alcohol', 'life_main', 'people_main', 'political', 'smoking', 'inspired_by']:
            item_name = 'personal_' + item
            data[item_name] = {
                'source_list': params[item_name].most_common(),
                'count': params[item_name].size
            }

        data['relation'] = {
            'source_list': params['relation'].most_common()
        }
        data['relatives'] = {
            'source_list': params['relatives'].most_common()
        }
        data['sex'] = {
            'man': params['sex'][2],
            'woman': params['sex'][1],
            'source_list': params['sex'].most_common()
        }
        data['verified'] = {
            'count': params['verified'].size
        }
        data['occupation_type'] = {
            'source_list': params['occupation_type'].most_common(),
            'count': params['occupation_type'].size
        }
        data['occupation_school'] = {
            'source_list': params['occupation'].get('school', TiedCounter([])).most_common(),
            'count': params['occupation'].get('school', TiedCounter([])).size
        }
        data['occupation_work'] = {
            'source_list': params['occupation'].get('work', TiedCounter([])).most_common(),
            'count': params['occupation'].get('work', TiedCounter([])).size
        }
        data['occupation_university'] = {
            'source_list': params['occupation'].get('university', TiedCounter([])).most_common(),
            'count': params['occupation'].get('university', TiedCounter([])).size
        }

        data['school'] = {
            'count': params['school'].size,
            'source_list': params['school'].most_common(ignore_single=True)
        }
        data['university'] = {
            'count': params['school'].size,
            'source_list': params['university'].most_common(ignore_single=True)
        }

        return data

    @cache_method
    def get_all_properties(self):

        data = self.process_data()

        properties = [
            self.gen_property_category(
                'age', 'Возраст',
                [
                    ('commonMean', 'Наисреднейший'),
                ],
                PLOT_LINE
            ),
            self.gen_property_category(
                'sex', 'Пол',
                [
                    ('man', 'Мужской'),
                    ('woman', 'Женский'),
                ],
                PLOT_CIRCULAR,
                self.gen_circular_plot(data['sex']['source_list'],
                                       name=lambda value: 'Мужской' if value.get_value() == 2 else 'Женский',
                                       color=lambda value: '#989FFF' if value.get_value() == 2 else '#FD8DA6')
            ),
            self.gen_property_category('city', 'Город', [], PLOT_CIRCULAR, common_count=3),
            # self.gen_property_category('group', 'Группы', [
            #     ('all_count', 'Уникальных групп'),
            #     ('mean_count', 'На человека')], None),
            self.gen_property_category('school', 'Школа', [], PLOT_CIRCULAR, common_count=5),
            self.gen_property_category('university', 'Университет (архив)', [], PLOT_CIRCULAR, common_count=5),
            self.gen_property_category('verified', 'Верификация', [('count', 'Количество')], None),
            self.gen_property_category('status', 'Статус', [], None),
            self.gen_property_category('site', 'Сайт', [], None),
            self.gen_property_category('phone', 'Телефон', [('mobile', 'Мобильный'), ('home', 'Домашний')], None),
            self.gen_property_category('country', 'Страна', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category('relatives', 'Среди родственников есть', [], PLOT_CIRCULAR,
                                       name_func=lambda x: relatives_dict[x],
                                       common_count=3),
            self.gen_property_category('occupation_type', 'Род занятий', [], PLOT_CIRCULAR,
                                       name_func=lambda x: occupation_type_dict[x],
                                       common_count=3),
            self.gen_property_category('occupation_work', 'Работа', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category('occupation_school', 'Текущая школа', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category('occupation_university', 'Университет', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category('personal_political', 'Политические предпочтения', [], PLOT_CIRCULAR,
                                       name_func=lambda x: political_dict.get(x),
                                       common_count=3),
            self.gen_property_category('personal_people_main', 'Главное в людях', [], PLOT_CIRCULAR,
                                       name_func=lambda x: people_main_dict[x],
                                       common_count=3),
            self.gen_property_category('personal_life_main', 'Главное в жизни', [], PLOT_CIRCULAR,
                                       name_func=lambda x: life_main_dict[x],
                                       common_count=3),
            self.gen_property_category('personal_smoking', 'Отношение к курению', [], PLOT_CIRCULAR,
                                       name_func=lambda x: smoking_dict[x],
                                       common_count=3),
            self.gen_property_category('personal_alcohol', 'Отношение к алкоголю', [], PLOT_CIRCULAR,
                                       name_func=lambda x: alcohol_dict[x],
                                       common_count=3),
            self.gen_property_category('relation', 'Семейное положение', [], PLOT_CIRCULAR,
                                       name_func=lambda x: relation_dict[x],
                                       common_count=5),
            self.gen_property_category('last_seen_time', 'Время последнего посещения (в днях)', [
                ('mean', 'Среднее'),
                ('max', 'Максимальное'),
                ('min', 'Минимальное'),
                ('median', 'Медианное'),
            ], PLOT_LINE),
            self.gen_property_category('home_town', 'Родной город', [], PLOT_CIRCULAR, common_count=3),
            self.gen_property_category(
                'is_closed', 'Статус аккаунта',
                [
                    ('opened', 'Открытый'),
                    ('closed', 'Приватный'),
                    ('banned', 'Забаненный'),
                    ('deleted', 'Удаленный'),
                ],
                PLOT_CIRCULAR,
                self.gen_circular_plot(data['is_closed']['source_list'],
                                       name=lambda
                                           x: account_status_dict.get(x, ['Неизвестный тип'])[0],
                                       color=lambda x: account_status_dict.get(x, ['#ffffff'])[1])),
            self.gen_property_category('online', 'Онлайн', [], PLOT_CIRCULAR, common_count=5),
            self.gen_property_category('personal_langs', 'Языки', [], PLOT_CIRCULAR, common_count=5),
            self.gen_property_category('personal_religion', 'Мировоззрение', [], PLOT_CIRCULAR, common_count=5),
            self.gen_property_category('last_seen_platform', 'Последнее посещение', [], PLOT_CIRCULAR, common_count=5,
                                       name_func=lambda x: last_seen_platform_dict[x]),
            self.gen_property_category('followers_count', 'Количество подписчиков',
                                       [
                                           ('max', 'Максимальное'),
                                           ('min', 'Минимальное'),
                                           ('mean', 'Среднее'),
                                           ('median', 'Медианное'),
                                       ], PLOT_LINE),
        ]
        return bool_filter(properties)

    def get_interesting_properties(self):
        all_props = self.get_all_properties()

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

    def get_important_properties(self):
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

    def get_description(self):
        return self.get_name() + f' ({self.size} чел.)'

    def get_entities(self):
        return {
            'connections': {
                VKUser.gen_id(first_id): [VKUser.gen_id(id_) for id_ in connected_list]
                for (first_id, connected_list) in
                self.get_connections().items()
            }
            ,
            'items': [user.get_entity() for user in self.objects],
        }

    def get_name(self):
        def n_persons_name():
            mod = self.size % 10
            persons_form = 'человек'
            if 2 <= mod <= 4:
                persons_form = 'человека'
            return f'{self.size} {persons_form}'

        if self.size == 1:
            return VKUser(self.data_list()[0]).name

        if self.target == 'friends':
            return 'Друзья ' + name_to_gent(self.main.full_data['first_name'])
        if self.target == 'loners':
            return 'Без кластера'
        if self.target == 'members':
            return f'Подписчики {self.main.name}'
        if self.target == 'search':
            return f'Поиск по: "{self.target_value}"'

        interesting_properties = self.get_interesting_properties()
        if interesting_properties:
            target = interesting_properties[0]
        else:
            return 'Пустой кластер'

        if target['value'].get('percent', 0) == 0:
            return n_persons_name()

        name = target['name']
        return name

    def get_query(self):
        if self.target == 'friends':
            return f"GET vk.user {self.main.full_data['screen_name']} friends"
        else:
            return f"GET vk.users ({' '.join(self.get_ids())})"

    def get_params(self, parent):
        return {
            'baseType': 'users',
            'service': 'vk',
            'type': 'community',
            'main': VKUser.gen_id(self.main),
            'fullEntitiesCount': 1,
            'id': self.hash,
            'name': self.get_name(),
            'query': self.get_query(),
            'prefix': 'vk.users',
            'parent': parent
        }

    def get_actions(self):
        actions = self.get_template_actions(split=True)
        actions += [
            {
                'id': 'groups',
                'name': 'Получить группы',
                'target': 'any',
                'value': 'groups'
            },
            {
                'id': 'friends',
                'name': 'Получить друзей',
                'target': 'one',
                'value': 'friends'
            },
        ]
        return actions

    def represent(self, force=False):
        self.preload(force)
        return {
            'clusters': {
                'items': [
                    self.main_cluster_data()
                ],
                'mainID': self.hash,
            },
        }

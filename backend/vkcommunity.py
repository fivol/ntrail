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

from many_objects import ManyObjects
from tied_counter import TiedCounter
from tied_value import TiedValue
from tools import once_property, find_phones, get_normal_phone_number, name_to_gent, concatenate_lists, \
    get_random_color, bool_filter, timeit, memorize
from vkgroup import VKGroups
import numpy as np
import networkx as nx
import collections
from collections import Counter
import datetime
from time import time
from vkuser import VKUser
import math
from itertools import groupby
from tools import clear_list, prepare_list, counter_top, get_sites, list_get, list_from_dicts, is_good_username
import re
from vkapi import VKAPI
import bisect
from constants import ACCOUNT_STATUS_PUBLIC, PLOT_LINE, PLOT_CIRCULAR

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


class VKCommunity(ManyObjects, VKAPI):
    base_class = VKUser
    available_attributes = ['friends']

    def __init__(self, users=None, main_user=None, clear=False, save_features=False, target=None, **kwargs):
        super().__init__()
        print(users)
        if isinstance(users, set):
            users = list(users)
        assert main_user is None or isinstance(main_user, VKUser), main_user
        self.main_user = main_user
        self.nodes = []
        self.counter = Counter()
        self.target = target

        if isinstance(users, Counter):
            self.counter = users
            self.nodes = [i[0] for i in self.counter.most_common()]
        elif isinstance(users, list):
            users = list(set(users))
            if users:
                if isinstance(users[0], VKUser):
                    self.nodes = [user.id for user in users]
                elif isinstance(users[0], int):
                    self.nodes = users
                elif isinstance(users[0], str):
                    usernames = [VKUser.get_username(url) for url in users]
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
        self.removed_nodes = []
        # if clear:
        #     clean_community = self.only_valid()
        #     self.removed_nodes = [node for node in self.nodes if node not in clean_community.nodes]
        #     self.nodes = clean_community.nodes
        #     self.counter = clean_community.counter
        if 3 < self.size < 800 and save_features:
            self.save_features()

        print('end init')

    @staticmethod
    def parse_usernames(usernames_string):
        usernames = re.findall(r'vk.com/([0-9a-z._]+)', usernames_string)
        return list(set(usernames))

    def get_deactivated(self):
        self.data_dict()
        return VKCommunity([user for user in self.objects if not user.valid], clear=False)

    def groups(self):
        all_groups = sum(
            filter(
                lambda x: isinstance(x, list), self.get_users_groups(self.nodes)),
            [])
        counter = Counter(all_groups)
        return VKGroups(counter)

    @once_property
    def short_info(self):
        return ''

    def data_list(self):
        return self.data_dict().values()

    @memorize
    def data_dict(self, force=False):
        data = self.get_users(self.nodes, full=True, force=force)
        return {
            item['id']: item
            for item in data
        }

    def friends(self):
        users_friends = self.get_users_friends(self.nodes)
        return VKCommunity(sum(filter(lambda x: isinstance(x, list), users_friends), []))

    def get_connections(self):
        connections = self.get_users_friends(self.nodes)
        return dict(zip(self.nodes, connections))

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

        def get_field_values(field, capitalize=False, clean=False):
            def prepare_value(value):
                if capitalize:
                    return value.capitalize()
                return value

            res = [
                TiedValue(prepare_value(user[field]), VKUser.gen_id(user['id']))
                for user in self.data_list()
                if field in user
            ]
            if clean:
                res = list(filter(lambda x: bool(x), res))
            return res

        def true_date(date_str):
            try:
                datetime.datetime.strptime(date_str, '%d.%m.%Y')
                return True
            except ValueError:
                return False

        for item_name in vk_connections_names:
            params['connection_' + item_name] = get_field_values(item_name)

        params['sex'] = TiedCounter(get_field_values('sex'))
        params['city'] = TiedCounter(list_from_dicts(get_field_values('city'), 'title'))
        params['country'] = TiedCounter(list_from_dicts(get_field_values('country'), 'title'))
        params['online'] = TiedCounter(get_field_values('online'))
        params['online_mobile'] = TiedCounter(get_field_values('online_mobile'))
        params['verified'] = TiedCounter(get_field_values('verified', clean=True))
        params['home_town'] = TiedCounter(get_field_values('home_town', capitalize=True, clean=True))
        params['online_app'] = TiedCounter(get_field_values('online_app'))
        params['followers_count'] = sorted(get_field_values('followers_count'))

        last_seen = get_field_values('last_seen')
        params['last_seen_platform'] = TiedCounter(list_from_dicts(last_seen, 'platform'))
        params['last_seen_time'] = sorted(list_from_dicts(last_seen, 'time'))

        params['mobile_phone'] = get_field_values('mobile_phone')
        params['home_phone'] = get_field_values('home_phone')
        params['site'] = get_field_values('site')
        params['status'] = get_field_values('status')
        params['relation'] = Counter(get_field_values('relation')).most_common()
        params['bdate'] = sorted([TiedValue(datetime.datetime.strptime(bdate.value, '%d.%m.%Y').timestamp(), bdate.id)
                                  for bdate in get_field_values('bdate') if
                                  len(bdate.value.split('.')) == 3])
        relatives_list = concatenate_lists(get_field_values('relatives'))
        params['relatives'] = Counter(list_from_dicts(relatives_list, 'type')).most_common()
        params['deactivated'] = TiedCounter(get_field_values('deactivated'))
        params['is_closed'] = TiedCounter(get_field_values('is_closed', clean=False))

        personal_list = get_field_values('personal')
        params['personal_langs'] = Counter(concatenate_lists(list_from_dicts(personal_list, 'langs'))).most_common()
        for item in ['smoking', 'people_main', 'life_main', 'alcohol', 'political', 'religion', 'inspired_by']:
            params['personal_' + item] = list_from_dicts(personal_list, item, counter=True, ignore_zero=True)

        occupation = sorted(get_field_values('occupation'), key=lambda x: x['type'])
        occupation_data = [
            (occupation_type, Counter(list_from_dicts(occupations, 'name')).most_common())
            for occupation_type, occupations in groupby(occupation, lambda x: x['type'])
        ]
        params['occupation'] = sorted(occupation_data, key=lambda x: -x[1][0][1])

        schools_list = sorted(concatenate_lists(get_field_values('schools')), key=lambda x: x['id'])

        schools_data = []
        # for school_id, schools in groupby(schools_list, lambda x: x['id']):
        #     schools = list(schools)
        #     school = schools[0]
        #     schools_data.append(
        #         {
        #             'count': len(schools),
        #             'id': school_id,
        #             'name': school['name'],
        #             'city': school['city'],
        #             'class': Counter(list_from_dicts(schools, 'class', ignore_zero=True)).most_common(),
        #             'year_from': Counter(list_from_dicts(schools, 'year_from', ignore_zero=True)).most_common(),
        #             'year_to': Counter(list_from_dicts(schools, 'year_to', ignore_zero=True)).most_common(),
        #             'year_graduated': Counter(list_from_dicts(schools,
        #                                                       'year_graduated', ignore_zero=True)).most_common(),
        #             'speciality': Counter(list_from_dicts(schools, 'speciality', ignore_zero=True)).most_common(),
        #             'type': school.get('type', ''),
        #             'country': school['country']
        #         }
        #     )
        # params['schools'] = sorted(schools_data, key=lambda x: -x['count'])
        #
        # universities_list = sorted(sum(list(get_field_values('universities')), []), key=lambda x: x['id'])
        # universities_data = []
        # for university_id, universities in groupby(universities_list, lambda x: x['id']):
        #     universities = list(universities)
        #     university = universities[0]
        #     universities_data.append(
        #         {
        #             'id': university_id,
        #             'count': len(universities),
        #             'name': university['name'],
        #             'faculty_name': Counter(list_from_dicts(universities, 'faculty_name')).most_common(),
        #             'chair_name': Counter(list_from_dicts(universities, 'chair_name')).most_common(),
        #             'graduation': Counter(list_from_dicts(universities, 'graduation')).most_common(),
        #             'education_form': Counter(list_from_dicts(universities, 'education_form')).most_common(),
        #             'education_status': Counter(list_from_dicts(universities, 'education_status')).most_common()
        #         }
        #     )
        # params['universities'] = sorted(universities_data, key=lambda x: -x['count'])

        return params

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

        all_ids_set = set(self.get_ids())

        age = sorted(time_delta(params['bdate'], dev=31536000))
        data['age'] = {
            'count': len(age),
            **prepare_list([item for item in age if (item.value > 6) & (item.value < 80)], clean=True),
            'source_list': age
        }
        data['followers_count'] = {
            **prepare_list(params['followers_count'], clean=True),
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
        last_seen = time_delta(params['last_seen_time'], dev=3600)
        data['last_seen_time'] = {
            **prepare_list(last_seen, count=False)
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
        data['status'] = {
            'count': len(params['status']),
            'len_median': np.median([len(status) for status in params['status']])
        }
        data['personal'] = {
            'alcohol': counter_top(params['personal_alcohol']),
            'langs': counter_top(params['personal_langs']),
            'life_main': counter_top(params['personal_life_main']),
            'people_main': counter_top(params['personal_people_main']),
            'political': counter_top(params['personal_political']),
            'religion': counter_top(params['personal_religion']),
            'smoking': counter_top(params['personal_smoking'])
        }

        data['relation'] = counter_top(params['relation'])
        data['relatives'] = params['relatives']
        data['sex'] = {
            'man': params['sex'][2],
            'woman': params['sex'][1],
            'source_list': params['sex'].most_common()
        }
        data['verified'] = {
            'count': params['verified'].size
        }
        # sites_sites = get_sites(' '.join(params['site']))
        # sites_status = get_sites(' '.join(params['status']))
        # sites = sites_sites + sites_status
        # data['site'] = {
        #     'site_count': len(params['site']),
        #     'site_good_count': len(sites_sites),
        #     'status_count': len(sites_status),
        #     'good_count': len(sites),
        #     'common_list': counter_top(Counter([item[0] for item in sites]).most_common())
        # }
        # usernames_dict = {}
        # for connection_site in vk_connections_names:
        #     usernames_list = prepare_username_list(list_get(sites, connection_site) +
        #                                            params['connection_' + connection_site],
        #                                            connection_site)
        #
        #     usernames_dict[connection_site] = {
        #         'list': usernames_list,
        #         'count': len(usernames_list)
        #     }
        # vk_usernames = prepare_username_list(list_get(sites, 'vk'), 'vk')
        # usernames_dict['vk'] = {
        #     'list': vk_usernames,
        #     'count': len(vk_usernames)
        # }
        # data['username'] = usernames_dict
        #
        # phones_list = params['home_phone'] + params['mobile_phone'] + find_phones(' '.join(params['status']))
        # phones_list = clear_list([get_normal_phone_number(phone) for phone in phones_list])
        # data['phone'] = {
        #     'list': phones_list,
        #     'count': len(phones_list)
        # }
        # schools_list = []
        # for i, school in enumerate(params['schools'][:3]):
        #     schools_list.append({
        #         'count': school['count'],
        #         'name': school['name'],
        #         'class': counter_top(school['class']),
        #         'year_from': np.median(school['year_from']),
        #         'year_to': np.median(school['year_to']),
        #         'speciality': counter_top(school['speciality']),
        #         'city': school['city'],
        #         'type': school['type']
        #     })
        # data['school'] = schools_list

        # universities_list = []
        # for i, university in enumerate(params['universities'][:3]):
        #     universities_list.append({
        #         'count': university['count'],
        #         'name': university['name'],
        #         'faculty_name': counter_top(university['faculty_name']),
        #         'chair_name': counter_top(university['chair_name']),
        #         'education_form': counter_top(university['education_form']),
        #         'education_status': counter_top(university['education_status']),
        #         'graduation': counter_top(university['graduation'])
        #     })
        # data['university'] = universities_list

        return data

    # @timeit
    def get_all_properties(self):
        default_props = [
            ('mean', 'Средний'),
            ('max', 'Максимальный'),
            ('min', 'Минимальный'),
            ('median', 'Медианный'),
            ('count', 'Указали')
        ]

        def gen_prop(id_, name_, value_, ids=None):
            if isinstance(value_, TiedValue):
                value_, ids = value_.value, value_.get_ids()
            if ids and len(ids) > 1:
                value_ = f'{value_} ({int(float(value_) / size * 100)} %)'

            if not value_ or (isinstance(value_, float) and np.isnan(value_)):
                return None
            return {
                'id': id_,
                'name': name_,
                'value': value_,
                'ids': ids
            }

        def gen_circular_plot(items, name=None, color=None):
            if color is None:
                color = lambda x: get_random_color()
            if name is None:
                name = lambda value: value.get_value()
            return [
                {
                    'value': count,
                    'ids': value.get_ids(),
                    'name': name(value),
                    'color': color(value)
                }
                for value, count in items if count > 0
            ]

        def gen_line_plot(items, name=None):
            return [
                {
                    'ids': item.get_ids(),
                    'value': round(item.get_value(), 2),
                    'name': data_dict[item.get_ids()[0]].get('name', 'Нет имени')
                }
                for item in items]

        def gen_plot(type_, data_list, key, name=None):
            if not type_:
                return None

            if not data_list:
                if type_ == PLOT_CIRCULAR:
                    data_list = gen_circular_plot(data[key]['source_list'], name=name)
                elif type_ == PLOT_LINE:
                    data_list = gen_line_plot(data[key]['source_list'])
                else:
                    return None

            if len(data_list) < 2:
                return None
            return {
                'type': type_,
                'data': data_list
            }

        def gen_property_category(key, name, props, plot_type=None, plot_data=None, common_count=0, name_func=None):
            if data[key].get('count', 1) == 0:
                return None
            base_id = f'{self.hash}_{key}'
            sup_properties = []

            if common_count:
                source_list = data[key]['source_list']
                for idx in range(common_count):
                    if len(source_list) > idx:
                        sub_prop_name = source_list[idx][0].value
                        if name_func:
                            sub_prop_name = name_func(sub_prop_name)
                        sup_properties.append(gen_prop(f'top_{idx}', sub_prop_name, source_list[idx][1],
                                                       source_list[idx][0].get_ids()))
            added_sub_keys = set()
            props += default_props
            for sub_property in props:
                sub_key = sub_property[0]
                if sub_key in data[key] and sub_key not in added_sub_keys:
                    added_sub_keys.add(sub_key)
                    sub_name = sub_property[1]
                    sub_value = data[key][sub_key]
                    sup_properties.append(gen_prop(sub_key, sub_name, sub_value))

            return {
                'id': base_id,
                'name': name,
                'plot': gen_plot(plot_type, plot_data, key, name=name_func),
                'values': bool_filter(sup_properties)
            }

        data = self.process_data()
        data_dict = self.data_dict()
        print([x[1] for x in data['online']['source_list']])
        size = data['size']
        account_status_dict = {
            0: ('Открытый', '#00682E'),
            1: ('Приватный', '#8D1E00'),
            'deleted': ('Удаленный', '#000000'),
            'banned': ('Забаненный', '#530742'),
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
        properties = [
            gen_property_category(
                'age', 'Возраст',
                [
                    ('commonMean', 'Наисреднейший'),
                ],
                PLOT_LINE,
                [{
                    'ids': item.get_ids(),
                    'value': round(item.get_value(), 2),
                    'name': VKUser(item.get_ids()[0]).name
                }
                    for item in data['age']['source_list']]
            ),
            gen_property_category(
                'sex', 'Пол',
                [
                    ('man', 'Мужской'),
                    ('woman', 'Женский'),
                ],
                PLOT_CIRCULAR,
                gen_circular_plot(data['sex']['source_list'],
                                  name=lambda value: 'Мужской' if value.get_value() == 2 else 'Женский',
                                  color=lambda value: '#989FFF' if value.get_value() == 2 else '#FD8DA6')

            ),
            gen_property_category('city', 'Город', [], PLOT_CIRCULAR, common_count=3),
            gen_property_category('verified', 'Верификация', [('count', 'Количество')], None),
            gen_property_category('country', 'Страна', [], PLOT_CIRCULAR, common_count=3),
            gen_property_category('home_town', 'Родной город', [], PLOT_CIRCULAR, common_count=3),
            gen_property_category(
                'is_closed', 'Статус аккаунта',
                [
                    ('opened', 'Открытый'),
                    ('closed', 'Приватный'),
                    ('banned', 'Забаненный'),
                    ('deleted', 'Удаленный'),
                ],
                PLOT_CIRCULAR,
                gen_circular_plot(data['is_closed']['source_list'],
                                  name=lambda
                                      x: account_status_dict.get(x, ['Неизвестный тип'])[0],
                                  color=lambda x: account_status_dict.get(x, ['#ffffff'])[1])),
            gen_property_category('online', 'Онлайн', [], PLOT_CIRCULAR, common_count=5),
            gen_property_category('last_seen_platform', 'Последнее посещение', [], PLOT_CIRCULAR, common_count=5,
                                  name_func=lambda x: last_seen_platform_dict[x]),
            gen_property_category('followers_count', 'Количество подписчиков',
                                  [
                                      ('count', 'Не нулевое'),
                                      ('max', 'Максимальное'),
                                      ('min', 'Минимальное'),
                                      ('mean', 'Среднее'),
                                      ('median', 'Медианное'),
                                  ], PLOT_LINE),
        ]
        return bool_filter(properties)

    @staticmethod
    def get_interesting_properties():
        return []

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

    def get_properties(self):
        print('get properties')
        return {
            'all': self.get_all_properties(),
            'interesting': self.get_interesting_properties(),
            'important': self.get_important_properties()
        }

    def get_entities(self):
        print('entities')
        return [user.get_entity() for user in self.objects]

    def preload(self, force=False):
        self.data_dict(force)

    def get_name(self):
        if self.target == 'friends':
            return 'Друзья ' + name_to_gent(self.main_user.full_data['first_name'])
        else:
            mod = self.size % 10
            persons_form = 'человек'
            if 2 <= mod <= 4:
                persons_form = 'человека'
            return f'{self.size} {persons_form}'

    def get_query(self):
        if self.target == 'friends':
            return f"GET vk.user {self.main_user.full_data['screen_name']} friends"
        else:
            return f"GET vk.users ({' '.join(self.get_ids())})"

    def get_params(self):
        print('get params')
        return {
            'baseType': 'users',
            'service': 'vk',
            'type': 'community',
            'main': VKUser.gen_id(self.main_user),
            'fullEntitiesCount': 1,
            'id': self.hash,
            'name': self.get_name(),
            'query': self.get_query()
        }

    def represent(self, force=False):
        self.preload(force)
        return {
            'clusters':
                [
                    {
                        'properties': self.get_properties(),
                        'params': self.get_params(),
                        'entities': self.get_entities(),
                        'id': self.hash
                    }
                ]
        }

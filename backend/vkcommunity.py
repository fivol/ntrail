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
from tools import once_property
from vkgroups import VKGroups
import numpy as np
import networkx as nx
import collections
from collections import Counter
import datetime
from time import time
from vkuser import VKUser
import math
from itertools import groupby
from tools import clear_list, prepare_list, counter_top, get_sites, list_get, list_from_dicts
import re
from vkapi import VKAPI
from db_logic import DB
import bisect
from constants import ACCOUNT_STATUS_PUBLIC

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

    def __init__(self, users=None, main_user=None, clear=False, save_features=True):
        super().__init__()
        if isinstance(users, set):
            users = list(users)
        assert main_user is None or isinstance(main_user, VKUser), main_user
        self.main_user = main_user
        self.nodes = []
        self.counter = Counter()

        if isinstance(users, Counter):
            self.counter = users
            self.nodes = [i[0] for i in self.counter.most_common()]
        elif isinstance(users, list) or isinstance(users, set):
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
        if clear:
            clean_community = self.only_valid()
            self.removed_nodes = [node for node in self.nodes if node not in clean_community.nodes]
            self.nodes = clean_community.nodes
            self.counter = clean_community.counter
        self.size = len(self.nodes)
        if 3 < self.size < 800 and save_features:
            self.save_features()

    @staticmethod
    def parse_usernames(usernames_string):
        usernames = re.findall(r'vk.com/([0-9a-z._]+)', usernames_string)
        return list(set(usernames))

    def get_deactivated(self):
        self.short_data
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

    def load_media_data(self, users=None):
        self.short_data

    @once_property
    def short_data(self):
        return self.get_users(self.nodes, full=False)

    @once_property
    def full_data(self):
        return self.get_users(self.nodes, full=True)

    def friends(self):
        users_friends = self.get_users_friends(self.nodes)
        return VKCommunity(sum(filter(lambda x: isinstance(x, list), users_friends), []))

    def get_connections(self):
        connections = self.get_users_friends(self.nodes)
        # print(connections)
        return dict(zip(self.nodes, connections))

    def only_valid(self):
        self.short_data
        return VKCommunity(
            Counter({user.id: self.counter[user.id] for user in self.objects if user.valid}),
            clear=False
        )

    def only_public(self):
        self.short_data
        return VKCommunity(
            Counter({user.id: self.counter[user.id]
                     for user in self.objects
                     if user.check_status() == ACCOUNT_STATUS_PUBLIC}),
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

    def process_data(self):
        params = self.params
        data = {
            'size': self.size
        }

        def time_delta(timestamp_list, dev=1):
            delta = time() - np.array(timestamp_list)
            delta = delta / dev
            return delta

        def prepare_username_list(username_list, service_name):
            usernames = []
            if service_name in ['vk', 'instagram', 'facebook', 'twitter']:
                for url in username_list:
                    url = url.strip('/ ')
                    site_items = url.split('/')
                    if len(site_items) > 1 and self.is_good_username(site_items[-1]):
                        usernames.append(site_items[-1])
                    elif len(site_items) == 1 and self.is_good_username(site_items[0]):
                        usernames.append(site_items[0])
            elif service_name in ['livejournal']:
                for url in username_list:
                    url = url.strip('/ ')
                    url = url.split('//')[-1]
                    site_items = url.split('.')
                    if len(site_items) == 3 and self.is_good_username(site_items[0]):
                        usernames.append(site_items[0])
                    elif len(site_items) == 1 and self.is_good_username(site_items[0]):
                        usernames.append(site_items[0])

            elif service_name in ['skype']:
                for username in username_list:
                    if self.is_good_username(username):
                        usernames.append(username)
            return clear_list(usernames)

        age = time_delta(params['bdate'], dev=31536000)
        data['age'] = {
            'all_count': len(age),
            **prepare_list(age[(age > 6) & (age < 80)], clean=True)
        }
        data['city'] = {
            'all_count': len(params['city']),
            'common_list': counter_top(params['city'])
        }
        data['country'] = {
            'all_count': len(params['country']),
            'common_list': counter_top(params['country'])
        }
        data['followers_count'] = {
            **prepare_list(params['followers_count'], clean=True),
        }
        data['home_town'] = {
            'all_count': len(params['home_town']),
            'common_list': counter_top(params['home_town'])
        }
        last_seen = time_delta(params['last_seen'], dev=3600)
        data['last_seen'] = {
            **prepare_list(last_seen)
        }
        data['online'] = {
            'count': params['online']
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
        data['sex'] = params['sex']
        data['verified'] = {
            'count': params['verified']
        }
        sites_sites = get_sites(' '.join(params['site']))
        sites_status = get_sites(' '.join(params['status']))
        sites = sites_sites + sites_status
        data['site'] = {
            'site_count': len(params['site']),
            'site_good_count': len(sites_sites),
            'status_count': len(sites_status),
            'good_count': len(sites),
            'common_list': counter_top(Counter([item[0] for item in sites]).most_common())
        }
        usernames_dict = {}
        for connection_site in vk_connections_names:
            usernames_list = prepare_username_list(list_get(sites, connection_site) +
                                                   params['connection_' + connection_site],
                                                   connection_site)

            usernames_dict[connection_site] = {
                'list': usernames_list,
                'count': len(usernames_list)
            }
        vk_usernames = prepare_username_list(list_get(sites, 'vk'), 'vk')
        usernames_dict['vk'] = {
            'list': vk_usernames,
            'count': len(vk_usernames)
        }
        data['username'] = usernames_dict

        phones_list = params['home_phone'] + params['mobile_phone'] + self.find_phones(' '.join(params['status']))
        phones_list = clear_list([self.get_normal_phone_number(phone) for phone in phones_list])
        data['phone'] = {
            'list': phones_list,
            'count': len(phones_list)
        }
        schools_list = []
        for i, school in enumerate(params['schools'][:3]):
            schools_list.append({
                'count': school['count'],
                'name': school['name'],
                'class': counter_top(school['class']),
                'year_from': np.median(school['year_from']),
                'year_to': np.median(school['year_to']),
                'speciality': counter_top(school['speciality']),
                'city': school['city'],
                'type': school['type']
            })
        data['school'] = schools_list

        universities_list = []
        for i, university in enumerate(params['universities'][:3]):
            universities_list.append({
                'count': university['count'],
                'name': university['name'],
                'faculty_name': counter_top(university['faculty_name']),
                'chair_name': counter_top(university['chair_name']),
                'education_form': counter_top(university['education_form']),
                'education_status': counter_top(university['education_status']),
                'graduation': counter_top(university['graduation'])
            })
        data['university'] = universities_list

        return data

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
                features[feature + '_count'] = sum_count

        for username, value in data['username'].items():
            features[f'username.{username}'] = value['count'] / size

        for i, university in enumerate(data['university'][:2]):
            features[f'university-{i}'] = university['count'] / size

        for i, school in enumerate(data['school'][:2]):
            features[f'school-{i}'] = school['count'] / size

        features = {key: value for key, value in features.items() if not np.isnan(value)}
        return features

    def collect_archive(self, count=200):
        assert isinstance(count, int)
        features = self.get_features()
        archive = DB.get_json_lines(count, 'vkcommunity')
        return {
            name: (value, sorted(list_from_dicts(archive, name)))
            for name, value in features.items()
        }

    def order_features(self, archive_size=200, version=1):
        assert isinstance(archive_size, int)
        assert isinstance(version, int)

        def calculate_priority(archive_list, value):
            # archive_list = sorted(list(set(archive_list)))
            ordered_list = archive_list
            if len(archive_list) < max(archive_size / 4, 50):
                return -1
            half_len = len(feature_list) // 2
            # print(len(ordered_list))
            if version == 0:
                index_left = bisect.bisect_left(ordered_list, value)
                index_right = bisect.bisect_right(ordered_list, value)
                if index_left <= half_len <= index_right:
                    return 0

                return min(abs(index_left - half_len),
                           abs(index_right - half_len)) \
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

    @once_property
    def params(self):
        params = {}

        def get_field_values(field):
            res = list(
                filter(
                    lambda x: bool(x),
                    [user[field]
                     for user in self.full_data
                     if field in user]
                )
            )
            return res

        def true_date(date_str):
            try:
                datetime.datetime.strptime(date_str, '%d.%m.%Y')
                return True
            except ValueError:
                return False

        for item_name in vk_connections_names:
            params['connection_' + item_name] = get_field_values(item_name)

        params['sex'] = Counter(get_field_values('sex')).most_common()
        params['mobile_phone'] = get_field_values('mobile_phone')
        params['home_phone'] = get_field_values('home_phone')
        params['city'] = list_from_dicts(get_field_values('city'), 'title', counter=True)
        params['country'] = list_from_dicts(get_field_values('country'), 'title', counter=True)
        params['online'] = sum(get_field_values('online'))
        params['online_mobile'] = sum(get_field_values('online_mobile'))
        params['verified'] = sum(get_field_values('verified'))
        params['last_seen'] = sorted(list_from_dicts(get_field_values('last_seen'), 'time'))
        params['site'] = get_field_values('site')
        params['followers_count'] = sorted(get_field_values('followers_count'), reverse=True)
        params['home_town'] = Counter(get_field_values('home_town')).most_common()
        params['status'] = get_field_values('status')
        params['relation'] = Counter(get_field_values('relation')).most_common()
        params['bdate'] = sorted([int(datetime.datetime.strptime(bdate, '%d.%m.%Y').timestamp())
                                  for bdate in get_field_values('bdate') if
                                  len(bdate.split('.')) == 3 and true_date(bdate)])

        relatives_list = sum(get_field_values('relatives'), [])
        params['relatives'] = Counter(list_from_dicts(relatives_list, 'type')).most_common()

        personal_list = get_field_values('personal')
        params['personal_langs'] = Counter(sum(list_from_dicts(personal_list, 'langs'), [])).most_common()
        for item in ['smoking', 'people_main', 'life_main', 'alcohol', 'political', 'religion', 'inspired_by']:
            params['personal_' + item] = list_from_dicts(personal_list, item, counter=True, ignore_zero=True)

        occupation = sorted(get_field_values('occupation'), key=lambda x: x['type'])
        occupation_data = [
            (occupation_type, Counter(list_from_dicts(occupations, 'name')).most_common())
            for occupation_type, occupations in groupby(occupation, lambda x: x['type'])
        ]
        params['occupation'] = sorted(occupation_data, key=lambda x: -x[1][0][1])

        schools_list = sorted(sum(get_field_values('schools'), []), key=lambda x: x['id'])

        schools_data = []
        for school_id, schools in groupby(schools_list, lambda x: x['id']):
            schools = list(schools)
            school = schools[0]
            schools_data.append(
                {
                    'count': len(schools),
                    'id': school_id,
                    'name': school['name'],
                    'city': school['city'],
                    'class': Counter(list_from_dicts(schools, 'class', ignore_zero=True)).most_common(),
                    'year_from': Counter(list_from_dicts(schools, 'year_from', ignore_zero=True)).most_common(),
                    'year_to': Counter(list_from_dicts(schools, 'year_to', ignore_zero=True)).most_common(),
                    'year_graduated': Counter(list_from_dicts(schools,
                                                              'year_graduated', ignore_zero=True)).most_common(),
                    'speciality': Counter(list_from_dicts(schools, 'speciality', ignore_zero=True)).most_common(),
                    'type': school.get('type', ''),
                    'country': school['country']
                }
            )
        params['schools'] = sorted(schools_data, key=lambda x: -x['count'])

        universities_list = sorted(sum(list(get_field_values('universities')), []), key=lambda x: x['id'])
        universities_data = []
        for university_id, universities in groupby(universities_list, lambda x: x['id']):
            universities = list(universities)
            university = universities[0]
            universities_data.append(
                {
                    'id': university_id,
                    'count': len(universities),
                    'name': university['name'],
                    'faculty_name': Counter(list_from_dicts(universities, 'faculty_name')).most_common(),
                    'chair_name': Counter(list_from_dicts(universities, 'chair_name')).most_common(),
                    'graduation': Counter(list_from_dicts(universities, 'graduation')).most_common(),
                    'education_form': Counter(list_from_dicts(universities, 'education_form')).most_common(),
                    'education_status': Counter(list_from_dicts(universities, 'education_status')).most_common()
                }
            )
        params['universities'] = sorted(universities_data, key=lambda x: -x['count'])

        return params

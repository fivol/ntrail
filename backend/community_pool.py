from baseapi import BaseAPI, bapi, once_property, timeit
from groups_pool import GroupsPool
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import collections
from collections import Counter
import datetime
from time import time
import functools
from vkuser import VKUser
import math
from itertools import groupby
import pandas as pd
from pprint import pprint


# @ - полное говнище, но надо куда нибудь прикрутить
# # - параметр обработан
# ! - доработать параметр


# '@photo_200', '@about', '@activities', '#bdate', '@books', '@career', '#city', '@connections',
# '#sex', '@contacts', '#country', '@education', '@exports', '#followers_count', '#home_town', '@interests',
# '#last_seen', '@maiden_name', '@military', '@movies', '@music', '@nickname', '!occupation', '#online',
# '#personal', '@quotes', '#relatives', '#relation', '!schools', '#site', '#status', '#trending', '#tv',
# '!universities', '#verified', '#counters'
# sex 2-man 1-woman


class Community(BaseAPI):

    def __init__(self, users=None, main_user=None):
        super().__init__()
        if isinstance(users, set):
            users = list(users)
        self.main_user = main_user
        if not users:
            ValueError('Users is empty')

        if isinstance(users, Counter):
            self.counter = users
            self.nodes = [item for item, count in users.most_common()]
        elif isinstance(users, list) or isinstance(users, set):
            users = list(set(users))
            if users:
                if isinstance(users[0], VKUser):
                    self.nodes = [user.id for user in users]
                elif isinstance(users[0], int):
                    self.nodes = users
                else:
                    raise TypeError()
            self.counter = Counter(self.nodes)
        else:
            raise TypeError('Wrong users type: {}'.format(type(users)))
        self.size = len(self.nodes)

    def __add__(self, other):
        return Community(self.counter + other.counter)

    @once_property
    def users(self):
        return [VKUser(user_id) for user_id in self.nodes]

    @once_property
    def groups(self):
        all_groups = sum(
            filter(
                lambda x: isinstance(x, list), self.get_users_groups(self.nodes)),
            [])
        counter = Counter(all_groups)
        return GroupsPool(counter)

    @once_property
    @timeit
    def graph(self):
        g = nx.Graph()
        self.get_users_friends(self.nodes)
        g.add_nodes_from(self.users)
        for user in self.users:
            friends = user.friends.nodes
            if friends:
                g.add_edges_from([(user.id, friend) for friend in friends if friend in self.nodes])
        return g

    def print(self, amount=None, shuffle=True):
        users = self.users.copy()
        self.short_data
        if shuffle and amount:
            np.random.shuffle(users)

        for user in users[:amount]:
            user.print()

    @once_property
    def short_info(self):
        return ''

    @once_property
    def short_data(self):
        return self.get_users(self.nodes, full=False)

    @once_property
    def full_data(self):
        return self.get_users(self.nodes, full=True)

    @classmethod
    def generate_random(cls, size):
        min_vkid = 1
        max_vkid = 420000000
        base = BaseAPI(verbose=0)
        ids_list = np.random.randint(min_vkid, max_vkid, size=size * 2)
        users = [x for x in base.get_users(ids_list, full=True).values() if 'deactivated' not in x]
        community_nodes_data = users[:size]
        nodes = [item['id'] for item in community_nodes_data]
        return cls(nodes)

    def connectedness(self):
        trs = nx.triangles(self.graph)
        ratio = math.log(1 + sum(trs.values()) / self.size)
        return ratio

    @classmethod
    def expand(cls, nodes_part, weight_reduction_ratio=0.95, break_point=10, max_nodes=300):
        community = set(nodes_part)
        bapi.get_users_friends(community)
        friends_counter = collections.Counter(
            sum([list(set(bapi.get_user_friends(user)) - set(community)) for user in community], []))
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
            unique_friends = set(bapi.get_user_friends(new_participant)) - set(community)
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

    @once_property
    def params(self):
        params = {}
        size = self.size

        def get_field_values(field):
            res = list(
                filter(
                    lambda x: bool(x),
                    [user[field]
                     for user in self.full_data.values()
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

        params['size'] = size
        params['sex'] = Counter(get_field_values('sex')).most_common()
        params['city_counter'] = self.list_from_dicts(get_field_values('city'), 'title', counter=True)
        params['country'] = self.list_from_dicts(get_field_values('country'), 'title', counter=True)
        params['online'] = sum(get_field_values('online'))
        params['online_mobile'] = sum(get_field_values('online_mobile'))
        params['verified'] = sum(get_field_values('verified'))
        params['last_seen'] = sorted(self.list_from_dicts(get_field_values('last_seen'), 'time'))
        params['site'] = get_field_values('site')
        params['followers_count'] = sorted(get_field_values('followers_count'), reverse=True)
        params['home_town'] = Counter(get_field_values('home_town')).most_common()
        params['status'] = get_field_values('status')
        params['relation'] = Counter(get_field_values('relation')).most_common()
        params['bdate'] = sorted([int(datetime.datetime.strptime(bdate, '%d.%m.%Y').timestamp())
                                  for bdate in get_field_values('bdate') if
                                  len(bdate.split('.')) == 3 and true_date(bdate)])

        relatives_list = sum(get_field_values('relatives'), [])
        params['relatives'] = Counter(self.list_from_dicts(relatives_list, 'type')).most_common()

        personal_list = get_field_values('personal')
        params['personal_langs'] = Counter(sum(self.list_from_dicts(personal_list, 'langs'), [])).most_common()
        for item in ['smoking', 'people_main', 'life_main', 'alcohol', 'political', 'religion', 'inspired_by']:
            params['personal_' + item] = self.list_from_dicts(personal_list, item, counter=True, ignore_zero=True)

        occupation = sorted(get_field_values('occupation'), key=lambda x: x['type'])
        occupation_data = [
            (occupation_type, Counter(self.list_from_dicts(occupations, 'name')).most_common())
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
                    'class': Counter(self.list_from_dicts(schools, 'class', ignore_zero=True)).most_common(),
                    'year_from': Counter(self.list_from_dicts(schools, 'year_from', ignore_zero=True)).most_common(),
                    'year_to': Counter(self.list_from_dicts(schools, 'year_to', ignore_zero=True)).most_common(),
                    'year_graduated': Counter(self.list_from_dicts(schools,
                                                                   'year_graduated', ignore_zero=True)).most_common(),
                    'speciality': Counter(self.list_from_dicts(schools, 'speciality', ignore_zero=True)).most_common(),
                    'type': school.get('type', ''),
                    'country': school['country']
                }
            )
        params['schools'] = sorted(schools_data, key=lambda x: -x['count'])
        # params['schools_type_str'] = self.list_from_dicts(schools_list, 'type_str', counter=True)
        # params['schools_year_from_median'] = np.median(self.list_from_dicts(schools_list, 'year_from'))
        # params['schools_year_to_median'] = np.median(self.list_from_dicts(schools_list, 'year_to'))

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
                    'faculty_name': Counter(self.list_from_dicts(universities, 'faculty_name')).most_common(),
                    'chair_name': Counter(self.list_from_dicts(universities, 'chair_name')).most_common(),
                    'graduation': Counter(self.list_from_dicts(universities, 'graduation')).most_common(),
                    'education_form': Counter(self.list_from_dicts(universities, 'education_form')).most_common(),
                    'education_status': Counter(self.list_from_dicts(universities, 'education_status')).most_common()
                }
            )
        params['universities'] = sorted(universities_data, key=lambda x: -x['count'])

        return params

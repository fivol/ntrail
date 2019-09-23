from baseapi import BaseAPI, bapi, once_property
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
import pandas as pd


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

            def get_user_id(user):
                if isinstance(user, VKUser):
                    return user.id
                return VKUser(user).id

            self.nodes = [get_user_id(user) for user in users]
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
    def graph(self):
        g = nx.Graph()
        self.get_users_friends(self.nodes)
        g.add_nodes_from(self.nodes)
        for user in self.users:
            friends = user.friends.nodes
            if friends:
                g.add_edges_from([(user, friend) for friend in friends if friend in self.nodes])
        return g

    def print(self, amount=None, shuffle=True):
        users = self.users.copy()
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
                     for user in self.short_data.values()
                     if field in user]
                )
            )
            if len(res) and not isinstance(res[0], list):
                return np.array(res)
            return res

        def count_list(list_obj, most_common=3, fr_name=None):
            result = Counter(list_obj).most_common(most_common)
            if fr_name:
                try:
                    params[f'{fr_name}_first_fr'] = result[0][1] / size
                except IndexError:
                    params[f'{fr_name}_first_fr'] = 0
            return result

        def generate_params(param_name=None, funcs=[], add_list=False, param_list=None):
            if param_list is None:
                param_list = get_field_values(param_name)

            for func in funcs:
                name = f'{param_name}_{func.__name__}'
                res = 0
                if len(param_list):
                    res = func(param_list)
                res = float(res)
                params[name] = res
            if add_list:
                params[f'{param_name}_list'] = sorted(param_list)

            return param_list

        def true_date(date_str):
            try:
                datetime.datetime.strptime(date_str, '%d.%m.%Y')
                return True
            except ValueError:
                return False

        params['size'] = size

        groups_comm = self.groups.from_most_common(75)
        groups_counter = groups_comm.counter
        groups_list = groups_comm.groups_data
        groups = count_list(groups_counter.elements(), most_common=10, fr_name='groups')

        groups_dict = self.dict_from_dicts(groups_list, 'id')
        smart_groups_sort = sorted(
            [
                (groups_counter[gr['id']] / math.log(gr['members_count']), gr['id'])
                for gr in groups_list if 'members_count' in gr
            ],
            reverse=True
        )[:10]

        for value, group_id in smart_groups_sort:
            group = groups_dict[group_id]
            group['smart_value'] = value
            amount = groups_counter[group_id]
            group['fr'] = amount / size
            group['amount'] = amount

        params['groups_smart_sort'] = [groups_dict[gid] for _, gid in smart_groups_sort]

        for group_id, amount in groups:
            group = groups_dict[group_id]
            group['amount'] = amount
            group['fr'] = amount / size

        params['groups'] = [groups_dict[gid] for gid, _ in groups]
        groups_params = groups_comm.params
        params.update(groups_params)

        params['groups_activity'] = self.list_from_dicts(groups_list, 'activity', counter=True,
                                                         most_common=5, fr_name='groups_activity')
        params['groups_activity_first'] = params['groups_activity'][0]
        params['groups_age_limits'] = self.list_from_dicts(groups_list, 'age_limits',
                                                           counter=True, fr_name='groups_age_limits')
        params['groups_age_limits_first'] = params['groups_age_limits'][0][0]
        params['groups_city'] = self.list_from_dicts(self.list_from_dicts(groups_list, 'city'), 'title', counter=True,
                                                     fr_name='groups_city')
        params['groups_country'] = self.list_from_dicts(list_from_dicts(groups_list, 'country'),
                                                        'title', counter=True)
        params['groups_has_photo'] = self.list_from_dicts(groups_list, 'has_photo', counter=True)
        params['groups_main_section'] = self.list_from_dicts(groups_list,
                                                             'main_section', counter=True, ignore_zero=True)
        params['groups_place'] = self.list_from_dicts(groups_list, 'title', counter=True)
        params['groups_verified'] = self.list_from_dicts(groups_list, 'verified',
                                                         counter=True, fr_name='groups_verified')
        generate_params(
            'groups_members_count',
            param_list=list_from_dicts(groups_list, 'members_count'),
            funcs=[np.mean, np.median, np.max])

        sex_list = generate_params('sex', funcs=[np.mean])
        params['mans_amount'] = (sex_list == 2).sum()
        params['womans_amount'] = (sex_list == 1).sum()

        bdate_list = np.array([datetime.datetime.strptime(bdate, '%d.%m.%Y').timestamp()
                               for bdate in get_field_values('bdate') if
                               len(bdate.split('.')) == 3 and true_date(bdate)])
        age_list = (time() - bdate_list) / (360 * 24 * 3600)
        age_list = age_list[(age_list > 3) & ((age_list < 90))]
        generate_params(param_name='age', param_list=age_list,
                        funcs=[np.median, np.mean, np.min, np.max, len], add_list=True)

        params['city_counter'] = list_from_dicts(get_field_values('city'), 'title', counter=True, fr_name='city')

        params['country_counter'] = list_from_dicts(
            get_field_values('country'), 'title', counter=True, fr_name='country')

        online_list = generate_params('online', funcs=[np.sum])
        params['online_mean'] = sum(online_list) / size

        online_mobile_list = generate_params('online_mobile', funcs=[np.sum])
        try:
            params['online_mobile_mean'] = len(online_mobile_list) / len(online_list)
        except ZeroDivisionError:
            params['online_mobile_mean'] = 0

        generate_params('verified', funcs=[np.sum, np.mean])

        last_seen_list = list_from_dicts(get_field_values('last_seen'), 'time')
        last_seen_list = (time() - last_seen_list) / (3600 * 24)
        generate_params('last_seen', param_list=last_seen_list, funcs=[np.mean, np.max, np.median])

        params['site'] = list(get_field_values('site'))
        params['site_fr'] = len(params['site']) / size

        generate_params('followers_count', funcs=[np.mean, np.median, np.max])

        params['home_town'] = count_list(get_field_values('home_town'), fr_name='home_town')

        occupation_list = get_field_values('occupation')
        params['occupation_type'] = list_from_dicts(
            occupation_list, 'type', counter=True, fr_name='occupation_type')
        params['occupation_name'] = list_from_dicts(
            occupation_list, 'name', counter=True, fr_name='occupation_name')

        personal_list = get_field_values('personal')
        params['personal_langs'] = count_list(
            functools.reduce((lambda x, y: list(x) + list(y)), list_from_dicts(personal_list, 'langs'), []),
            fr_name='personal_langs')
        for item in ['smoking', 'people_main', 'life_main', 'alcohol', 'political', 'religion', 'inspired_by']:
            params['personal_' + item] = list_from_dicts(
                personal_list, item, counter=True, ignore_zero=True, fr_name=f'personal_{item}')

        relatives_list = sum(get_field_values('relatives'), [])
        params['relatives_childs'] = len(list_from_dicts(relatives_list, 'child'))
        params['relatives_childs_fr'] = params['relatives_childs'] / size

        params['relation'] = count_list(get_field_values('relation'), fr_name='relation')

        schools_list = sum(get_field_values('schools'), [])
        schools_dict = dict([(school['id'], school) for school in schools_list])
        fr_schools_ids = list_from_dicts(schools_list, 'id', counter=True, fr_name='schools')
        for school, amount in fr_schools_ids:
            schools_dict[school]['amount'] = amount
            schools_dict[school]['fr'] = amount / size
        params['schools'] = [schools_dict[school_id[0]] for school_id in list(fr_schools_ids)]
        params['schools_type_str'] = list_from_dicts(schools_list, 'type_str', counter=True,
                                                          fr_name='schools_type_str')
        # params['schools_year_from'] = list_from_dicts(schools_list, 'year_from')
        params['schools_year_from_median'] = np.median(list_from_dicts(schools_list, 'year_from'))
        # params['schools_year_to'] = list_from_dicts(schools_list, 'year_to')
        params['schools_year_to_median'] = np.median(list_from_dicts(schools_list, 'year_to'))

        status_list = get_field_values('status')
        params['status_fr'] = len(status_list) / size

        universities_list = list(get_field_values('universities'))
        universities_list = functools.reduce((lambda x, y: list(x) + list(y)), universities_list, [])
        params['universities_name'] = list_from_dicts(universities_list, 'name', counter=True,
                                                           fr_name='universities')
        params['universities_faculty_name'] = list_from_dicts(
            universities_list, 'faculty_name', counter=True, fr_name='universities_faculty_name')

        return params

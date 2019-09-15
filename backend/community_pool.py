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

    def __init__(self, nodes=None, nodes_data=None, verbose=0):
        super().__init__(verbose)
        if nodes_data:
            if not isinstance(nodes_data, dict):
                raise TypeError('nodes_data must be dict')
            nodes = nodes_data.values()
        if not (isinstance(nodes, list) or isinstance(nodes, set)):
            raise TypeError('nodes must be list or set')
        if not nodes:
            ValueError('nodes do not specified')
        self.nodes = list(nodes)
        self.nodes_data = nodes_data
        self.size = len(self.nodes)
        self.verbose = verbose

    @once_property
    def users(self):
        return [VKUser(vkid) for vkid in self.nodes]

    @once_property
    def graph_nodes(self):
        return self.graph.nodes

    def set_verbose(self, verbose):
        self.verbose = verbose
        super(BaseAPI).verbose = verbose

    @once_property
    def groups(self):
        all_groups = sum(
            filter(
                lambda x: isinstance(x, list), self.get_users_groups(self.nodes)),
            [])
        counter = Counter(all_groups)
        return GroupsPool.from_counter(counter)

    @once_property
    def graph(self):
        G = nx.Graph()
        self.get_users_friends(self.nodes)
        G.add_nodes_from(self.nodes)
        for user in self.nodes:
            friends = self.get_user_friends(user)
            if friends:
                G.add_edges_from([(user, friend) for friend in friends if friend in self.nodes])
        return G

    def print(self, amount=None):
        self.get_users(self.nodes)
        users = list(self.users)
        if amount:
            np.random.shuffle(users)

        for user in users[:amount]:
            user.print()

    @once_property
    def short_info(self):
        return ''

    @once_property
    def users_data(self):
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
        return cls(nodes=nodes)

    def expand_community(self, **kwargs):
        return self.from_nodes_part(self.nodes, **kwargs)

    def connectedness(self):
        trs = nx.triangles(self.graph)
        coef = math.log(1 + sum(trs.values()) / self.size)
        return coef

    @classmethod
    def from_nodes_part(cls, nodes_part, weight_reduction_ratio=0.95, break_point=10, max_nodes=300):
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
        return cls(nodes=community)

    def get_special_params(self):
        comm_params = self.params

        def check_special_param(k, v):
            try:
                int(v)
                return True
            except:
                return False

        return {key: value for key, value in comm_params.items() if check_special_param(key, value)}

    def get_field_values(self, field):
        res = list(
            filter(
                lambda x: bool(x),
                [user[field]
                 for user in self.users_data.values()
                 if field in user]
            )
        )
        if len(res) and not isinstance(res[0], list):
            return np.array(res)
        return res

    @once_property
    def params(self):
        comm_params = {}
        size = len(self.nodes)
        get_field_values = self.get_field_values

        def count_list(list_obj, most_common=3, fr_name=None):
            result = Counter(list_obj).most_common(most_common)
            if fr_name:
                try:
                    comm_params[f'{fr_name}_first_fr'] = result[0][1] / size
                except IndexError:
                    comm_params[f'{fr_name}_first_fr'] = 0
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
                comm_params[name] = res
            if add_list:
                comm_params[f'{param_name}_list'] = sorted(param_list)

            return param_list

        def add_frequency_param(param_name):
            comm_params[f'{param_name}_frequency'] = comm_params[param_name] / size

        def list_from_dicts(dicts_list, key, counter=False, most_common=3, fr_name=None, ignore_zero=False):
            dicts_list = filter(lambda x: key in x, dicts_list)
            result = map(lambda x: x[key], dicts_list)
            if ignore_zero:
                result = filter(lambda x: bool(x), result)
            if counter:
                return count_list(result, most_common=most_common, fr_name=fr_name)
            return np.array(list(result))

        def true_date(date_str):
            try:
                datetime.datetime.strptime(date_str, '%d.%m.%Y')
                return True
            except ValueError:
                return False

        comm_params['community_size'] = size

        # add groups params from Groups class. All groups of community participants
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

        comm_params['groups_smart_sort'] = [groups_dict[gid] for _, gid in smart_groups_sort]

        for group_id, amount in groups:
            group = groups_dict[group_id]
            group['amount'] = amount
            group['fr'] = amount / size

        comm_params['groups'] = [groups_dict[gid] for gid, _ in groups]
        groups_params = groups_comm.params
        comm_params.update(groups_params)

        comm_params['groups_activity'] = list_from_dicts(groups_list, 'activity', counter=True,
                                                         most_common=5, fr_name='groups_activity')
        comm_params['groups_activity_first'] = comm_params['groups_activity'][0]
        comm_params['groups_age_limits'] = list_from_dicts(groups_list, 'age_limits',
                                                           counter=True, fr_name='groups_age_limits')
        comm_params['groups_age_limits_first'] = comm_params['groups_age_limits'][0][0]
        comm_params['groups_city'] = list_from_dicts(list_from_dicts(groups_list, 'city'), 'title', counter=True,
                                                     fr_name='groups_city')
        comm_params['groups_country'] = list_from_dicts(list_from_dicts(groups_list, 'country'),
                                                        'title', counter=True)
        comm_params['groups_has_photo'] = list_from_dicts(groups_list, 'has_photo', counter=True)
        comm_params['groups_main_section'] = list_from_dicts(groups_list,
                                                             'main_section', counter=True, ignore_zero=True)
        comm_params['groups_place'] = list_from_dicts(groups_list, 'title', counter=True)
        comm_params['groups_verified'] = list_from_dicts(groups_list, 'verified',
                                                         counter=True, fr_name='groups_verified')
        generate_params(
            'groups_members_count',
            param_list=list_from_dicts(groups_list, 'members_count'),
            funcs=[np.mean, np.median, np.max])

        sex_list = generate_params('sex', funcs=[np.mean])
        comm_params['mans_amount'] = (sex_list == 2).sum()
        comm_params['womans_amount'] = (sex_list == 1).sum()

        bdate_list = np.array([datetime.datetime.strptime(bdate, '%d.%m.%Y').timestamp()
                               for bdate in get_field_values('bdate') if
                               len(bdate.split('.')) == 3 and true_date(bdate)])
        age_list = (time() - bdate_list) / (360 * 24 * 3600)
        age_list = age_list[(age_list > 3) & ((age_list < 90))]
        generate_params(param_name='age', param_list=age_list,
                        funcs=[np.median, np.mean, np.min, np.max, len], add_list=True)

        comm_params['city_counter'] = list_from_dicts(get_field_values('city'), 'title', counter=True, fr_name='city')

        comm_params['country_counter'] = list_from_dicts(
            get_field_values('country'), 'title', counter=True, fr_name='country')

        online_list = generate_params('online', funcs=[np.sum])
        comm_params['online_mean'] = sum(online_list) / size

        online_mobile_list = generate_params('online_mobile', funcs=[np.sum])
        try:
            comm_params['online_mobile_mean'] = len(online_mobile_list) / len(online_list)
        except ZeroDivisionError:
            comm_params['online_mobile_mean'] = 0

        generate_params('verified', funcs=[np.sum, np.mean])

        last_seen_list = list_from_dicts(get_field_values('last_seen'), 'time')
        last_seen_list = (time() - last_seen_list) / (3600 * 24)
        generate_params('last_seen', param_list=last_seen_list, funcs=[np.mean, np.max, np.median])

        comm_params['site'] = list(get_field_values('site'))
        comm_params['site_fr'] = len(comm_params['site']) / size

        generate_params('followers_count', funcs=[np.mean, np.median, np.max])

        comm_params['home_town'] = count_list(get_field_values('home_town'), fr_name='home_town')

        occupation_list = get_field_values('occupation')
        comm_params['occupation_type'] = list_from_dicts(
            occupation_list, 'type', counter=True, fr_name='occupation_type')
        comm_params['occupation_name'] = list_from_dicts(
            occupation_list, 'name', counter=True, fr_name='occupation_name')

        personal_list = get_field_values('personal')
        comm_params['personal_langs'] = count_list(
            functools.reduce((lambda x, y: list(x) + list(y)), list_from_dicts(personal_list, 'langs'), []),
            fr_name='personal_langs')
        for item in ['smoking', 'people_main', 'life_main', 'alcohol', 'political', 'religion', 'inspired_by']:
            comm_params['personal_' + item] = list_from_dicts(
                personal_list, item, counter=True, ignore_zero=True, fr_name=f'personal_{item}')

        relatives_list = sum(get_field_values('relatives'), [])
        comm_params['relatives_childs'] = len(list_from_dicts(relatives_list, 'child'))
        comm_params['relatives_childs_fr'] = comm_params['relatives_childs'] / size

        comm_params['relation'] = count_list(get_field_values('relation'), fr_name='relation')

        schools_list = sum(get_field_values('schools'), [])
        schools_dict = dict([(school['id'], school) for school in schools_list])
        fr_schools_ids = list_from_dicts(schools_list, 'id', counter=True, fr_name='schools')
        for school, amount in fr_schools_ids:
            schools_dict[school]['amount'] = amount
            schools_dict[school]['fr'] = amount / size
        comm_params['schools'] = [schools_dict[school_id[0]] for school_id in list(fr_schools_ids)]
        comm_params['schools_type_str'] = list_from_dicts(schools_list, 'type_str', counter=True,
                                                          fr_name='schools_type_str')
        # comm_params['schools_year_from'] = list_from_dicts(schools_list, 'year_from')
        comm_params['schools_year_from_median'] = np.median(list_from_dicts(schools_list, 'year_from'))
        # comm_params['schools_year_to'] = list_from_dicts(schools_list, 'year_to')
        comm_params['schools_year_to_median'] = np.median(list_from_dicts(schools_list, 'year_to'))

        status_list = get_field_values('status')
        comm_params['status_fr'] = len(status_list) / size

        universities_list = list(get_field_values('universities'))
        universities_list = functools.reduce((lambda x, y: list(x) + list(y)), universities_list, [])
        comm_params['universities_name'] = list_from_dicts(universities_list, 'name', counter=True,
                                                           fr_name='universities')
        comm_params['universities_faculty_name'] = list_from_dicts(
            universities_list, 'faculty_name', counter=True, fr_name='universities_faculty_name')

        return comm_params

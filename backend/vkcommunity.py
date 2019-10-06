from many_objects import ManyObjects
from tools import once_property, timeit
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


class VKCommunity(ManyObjects):
    @timeit
    def __init__(self, users=None, main_user=None):
        super().__init__()
        self.base_class = VKUser
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

    @once_property
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
        return self.__class__(self.get_users_friends(self.nodes), [])

    def get_connections(self):
        connections = self.get_users_friends(self.nodes)
        return dict(zip(self.nodes, connections))

    @classmethod
    def generate_random(cls, size):
        min_vkid = 1
        max_vkid = 420000000
        ids_list = np.random.randint(min_vkid, max_vkid, size=size * 2)
        users = [x for x in cls.get_users(ids_list, full=True).values() if 'deactivated' not in x]
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

    def shorten_data(self):
        params = self.params
        data = {}

        def time_delta(timestamp_list, dev=1):
            delta = time() - np.array(timestamp_list)
            delta = delta / dev
            return delta

        def prepare_username_list(username_list, service_name):
            return list(set(username_list))

        age = time_delta(params['bdate'], dev=31536000)
        data['age_all_count'] = len(age)
        data.update(self.prepare_list(age[(age > 6) & (age < 90)], 'age', clean=True))
        data['city_all_count'] = len(params['city'])
        data['city'] = self.counter_top(params['city'])
        data['country_all_count'] = len(params['country'])
        data['country'] = self.counter_top(params['country'])
        data.update(self.prepare_list(params['followers_count'], 'followers_count', clean=True))
        data['home_town_all_count'] = len(params['home_town'])
        data['home_town'] = self.counter_top(params['home_town'])
        last_seen = time_delta(params['last_seen'], dev=3600)
        data.update(self.prepare_list(last_seen, 'last_seen'))
        data['online'] = params['online']
        data['online_mobile'] = params['online_mobile']
        data['personal_alcohol'] = self.counter_top(params['personal_alcohol'])
        # occupation personal_inspired_by schools status universities
        # ? personal_religion relation
        data['personal_langs'] = self.counter_top(params['personal_langs'])
        data['personal_life_main'] = self.counter_top(params['personal_life_main'])
        data['personal_people_main'] = self.counter_top(params['personal_people_main'])
        data['personal_political'] = self.counter_top(params['personal_political'])
        data['personal_religion'] = self.counter_top(params['personal_religion'])
        data['personal_smoking'] = self.counter_top(params['personal_smoking'])
        data['relation'] = self.counter_top(params['relation'])
        data['relatives'] = params['relatives']
        data['sex'] = params['sex']
        data['verified'] = params['verified']
        sites_sites = sum([self.get_sites(url_string) for url_string in params['site']], [])
        sites_status = sum([self.get_sites(url_string) for url_string in params['status']], [])
        sites = sites_sites + sites_status
        data['site_common'] = self.counter_top(Counter([item[0] for item in sites]).most_common())
        username = [url.split('/') for url in self.list_get(sites, 'instagram')]
        instagram_username = params['instagram']
        data['username_instagram'] = prepare_username_list(
            [item[-1] if item[-1] else item[-2] for item in username] + instagram_username, 'instagram')
        vkid= [url.split('/') for url in self.list_get(sites, 'vk')]
        data['vk_id'] = [item[-1] if item[-1] else item[-2] for item in vkid]
        data['site_facebook'] = self.list_get(sites, 'facebook')
        data['site_twitter'] = self.list_get(sites, 'twitter')
        data['site_site_count'] = len(params['site'])
        data['site_site_good_count'] = len(sites_sites)
        data['site_status_count'] = len(sites_status)
        data['site_good_count'] = len(sites)

        return data

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

        for item_name in vk_connections_names:
            params[item_name] = get_field_values(item_name)

        params['sex'] = Counter(get_field_values('sex')).most_common()
        params['city'] = self.list_from_dicts(get_field_values('city'), 'title', counter=True)
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

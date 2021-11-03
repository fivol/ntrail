from functools import cache
import numpy as np
import networkx as nx
import collections
from more_itertools import unique_everseen

from worker import VkMethods
from core.modules.vk.vkgroup import VKGroup
from core.modules.vk.vkgroups import VKGroups
from core.module.represent import try_base_analog, Represent
from core.module.represent_tools import RepresentTools
from core.helpers.utils import *
from core.modules.vk.vkuser import VKUser
from core.helpers.utils import clear_list


class VKCommunity(Represent, RepresentTools):
    _single_media_cls = VKUser

    def __init__(self, users=None, main=None, clear=False, save_features=False, target=None, target_value=None, **kwargs):
        super().__init__()
        self.target_value = target_value
        if isinstance(users, set):
            users = list(users)
        assert main is None or isinstance(main, VKUser) or isinstance(main, VKGroup), main
        self.main = main
        self.ids = []
        self._counter = Counter()
        self.target = target

        if isinstance(users, Counter):
            self._counter = users
            self.ids = [i[0] for i in self.counter.most_common()]
        elif isinstance(users, list):
            users = list(filter(lambda x: x is not None, unique_everseen(users)))
            if users:
                if isinstance(users[0], VKUser):
                    self.ids = [user.id for user in users]
                elif isinstance(users[0], int):
                    self.ids = users
                elif isinstance(users[0], str):
                    id_ = VKUser._parse_id(users[0])
                    if id_:
                        self.ids = [VKUser._parse_id(id_) for id_ in users]
                    else:
                        usernames = [VKUser._extract_username(url) for url in users]
                        usernames = clear_list(usernames)
                        VkMethods.resolve.sync(usernames)
                        self.ids = [VKUser(username).id for username in usernames]
                        self.ids = clear_list(self.ids)
                else:
                    raise TypeError('user instance must be int or string, but' + str(type(users[0])))
            self._counter = Counter(self.ids)
        elif isinstance(users, str):
            usernames = VKCommunity.parse_usernames(users)
            VkMethods.resolve.sync_map(usernames)
            self.ids = [VKUser(username).id for username in usernames]
            self.ids = clear_list(self.ids)
            self._counter = Counter(self.ids)
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
                lambda x: isinstance(x, list), self.get_users_groups(self.ids)),
            [])
        return VKGroups(all_groups_ids)

    @try_base_analog
    def groups(self):
        all_groups = sum(
            filter(
                lambda x: isinstance(x, list), self.get_users_groups(self.ids)),
            [])

        counter = Counter(all_groups)
        groups = VKGroups(counter).select()
        groups_order = groups.order()
        top_groups = groups_order.select(50)
        return top_groups

    def short_info(self):
        return ''

    @cache
    def data(self, force=False, full=True):
        return VkMethods.users.sync(self.ids, full=full)

    @try_base_analog
    def friends(self):
        users_friends = VkMethods.friends.sync_map(self.ids)
        users_friends += [self.ids]
        return VKCommunity(sum(filter(lambda x: isinstance(x, list), users_friends), []))

    def get_connections(self):
        connections = self.get_users_friends(self.ids)
        return {
            first_id: [second_id for second_id in connected_list if second_id in self.ids]
            for (first_id, connected_list) in zip(self.ids, connections)
        }

    def only_valid(self):
        self.preload()
        return VKCommunity(
            Counter({user.id: self.counter[user.id] for user in self.objects if user.valid}),
            clear=False
        )

    @classmethod
    def random(cls, size):
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

    @classmethod
    def search_query(cls, search_str):
        return VKCommunity(
            list(map(lambda x: x['profile']['id'],
                     filter(lambda x: x['type'] == 'profile',
                            cls.search(search_str, limit=20)['items']))),
            target='search',
            target_value=search_str
        )

    def get_description(self):
        return self.name + f' ({self.size} чел.)'

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

    @property
    def name(self):
        def n_persons_name():
            mod = self.size % 10
            persons_form = 'человек'
            if 2 <= mod <= 4:
                persons_form = 'человека'
            return f'{self.size} {persons_form}'

        if self.size == 1:
            return VKUser(self.data_list()[0]).name

        if self.target == 'friends':
            return 'Друзья ' + name_to_gent(self.main.data()['first_name'])
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
            'name': self.name,
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

    def connections(self):
        pass

    def summary(self) -> dict:
        return {}

    def counter(self) -> Counter:
        return self._counter

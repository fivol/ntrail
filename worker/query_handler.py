from core.call_worker.query_object import ComplexQuery, BasicQuery
from collections import defaultdict
from core.module.tools import split_list
from core.call_worker.api_errors import APIError

# Принимает список базовых запросов. Задача максимально оптимально создать
# составные запросы для наибыстрейшего выполнение всех

group_fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                'main_section', 'members_count', 'place',
                'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                'description', 'site', 'start_date']
groups_fields_string = ','.join(group_fields)
user_fields = ['photo_200', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
               'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
               'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
               'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
               'universities', 'verified', 'counters', 'screen_name', 'lists', 'is_closed', ]

users_fields_string = ','.join(user_fields)
service_token_methods = {'friends', 'resolve', 'friends', 'user_short', 'group_short', 'wall', 'posts', 'albums_ids',
                         'apps'}

user_token_methods = {'groups', 'search', 'members',
                      'user_full', 'group_full', 'photos_ids'}

methods_group_key = {'user_short', 'user_full', 'group_short', 'group_full', 'posts', 'photos_ids', 'albums_ids',
                     'apps'}

available_execute = {'friends', 'groups', 'resolve', 'members'}

execute_queries_count = 25
service_token_queries_count = 26  # 20
user_token_queries_count = 5  # 3

assert not len(methods_group_key -
               user_token_methods -
               service_token_methods)

assert not len(service_token_methods & user_token_methods)

assert not len(available_execute - user_token_methods - service_token_methods)


class VKHandler:
    service = 'vk'

    @classmethod
    def combine_queries(cls, methods_dict):
        complex_queries = []
        for method, queries in methods_dict.items():
            if not queries:
                continue
            if method in methods_group_key:
                limit = 10000
                if method.startswith('user_'):
                    limit = 900  # 1000
                if method.startswith('group_'):
                    limit = 400  # 500

                all_keys = [query.key for query in queries]
                keys_list = split_list(all_keys, limit)
                queries_list = split_list(queries, limit)
                for keys_segment, queries_segment in zip(keys_list, queries_list):
                    complex_queries.append(
                        ComplexQuery(cls.service, method, keys_segment,
                                     queries=queries_segment, convert_type=1,
                                     access_token=next(iter(queries)).access_token)
                    )
            else:
                complex_queries += [ComplexQuery.from_basic_query(query) for query in queries]

        return complex_queries

    @staticmethod
    def generate_execute_string(queries):
        def query_execute_str(query):
            if query.method == 'friends':
                return 'API.friends.get({"user_id":%d})' % int(query.key)
            if query.method == 'groups':
                return 'API.groups.get({"user_id":%d})' % int(query.key)
            if query.method == 'resolve':
                return 'API.utils.resolveScreenName({"screen_name":"%s"})' % query.key
            if query.method == 'group_full':
                assert isinstance(query.key, list)
                return 'API.groups.getById({"fields":"' + groups_fields_string + '","group_ids":"%s"})' % query.key
            if query.method == 'user_full':
                assert isinstance(query.key, list)
                return 'API.users.get({"fields":"' + users_fields_string + '","user_ids":"%s"})' % ','.join(query.key)
            if query.method == 'members':
                return 'API.groups.getById({"group_id":"%s","offset":"%s","count":"%s"})' % (
                    query.key, query.params.get('offset', 0), query.params.get('count', 200))

            raise NotImplementedError(query.method)

        assert len(queries) <= 25
        query_strings = [query_execute_str(query) for query in queries]
        code_string = f'return [{",".join(query_strings)}];'
        return code_string

    @classmethod
    def calculate_execute(cls, to_execute):
        execute_queries_bunches = split_list(to_execute, execute_queries_count)
        execute_queries = []
        for query_bunch in execute_queries_bunches:
            execute_string = cls.generate_execute_string(query_bunch)
            query = ComplexQuery(cls.service, 'execute', execute_string,
                                 queries=query_bunch,
                                 convert_type=2)
            execute_queries.append(query)

        return execute_queries

    @classmethod
    def get_queries_to_execute(cls, complex_queries_all):
        service_fast_count = round(execute_queries_count * user_token_queries_count / service_token_queries_count)
        non_execute = [query for query in complex_queries_all if query.method not in available_execute]
        complex_queries = [query for query in complex_queries_all if query.method in available_execute]
        user_token_queries = [query for query in complex_queries if query.method in user_token_methods]
        service_token_queries = [query for query in complex_queries if query.method in service_token_methods]
        to_execute = []
        other = []
        mod_service_tokens = len(service_token_queries) % execute_queries_count
        if mod_service_tokens > service_fast_count:
            to_execute += service_token_queries
        else:
            other += service_token_queries[:mod_service_tokens]
            to_execute += service_token_queries[mod_service_tokens:]

        user_queries_count = len(user_token_queries)
        if user_queries_count > 1:
            if (user_queries_count + len(to_execute)) % execute_queries_count == 1 \
                    and len(to_execute):
                other += to_execute[0]
                to_execute = to_execute[1:] + user_token_queries
            else:
                to_execute += user_token_queries
        else:
            other += user_token_queries

        return to_execute, other + non_execute

    @classmethod
    def encode(cls, queries):
        assert isinstance(queries, list)
        assert len(queries)
        assert isinstance(queries[0], BasicQuery)

        methods_dict = defaultdict(list)
        for query in queries:
            methods_dict[query.method].append(query)

        complex_queries = cls.combine_queries(methods_dict)
        assert len(complex_queries)
        assert isinstance(complex_queries, list)
        to_execute_queries, other_queries = cls.get_queries_to_execute(complex_queries)
        assert len(to_execute_queries) + len(other_queries) == len(complex_queries)
        complex_queries = cls.calculate_execute(to_execute_queries)
        if complex_queries:
            assert isinstance(complex_queries, list)
            assert isinstance(next(iter(complex_queries)), ComplexQuery)
        complex_queries += other_queries

        assert len(complex_queries)
        assert isinstance(complex_queries, list)
        cls.complex_queries = list(complex_queries)
        return cls.complex_queries

    @classmethod
    def decode(cls, complex_query):
        assert isinstance(complex_query, ComplexQuery)
        convert_type = complex_query.convert_type
        if convert_type == 0:
            query = complex_query.basic_queries[0]
            query.set_value(complex_query.value)
            res = [query]
        elif convert_type == 1 or convert_type == 2:
            queries = complex_query.basic_queries
            values = complex_query.value
            if APIError.is_error(values):
                values = [values] * len(queries)
            assert isinstance(queries, list)
            assert isinstance(values, list), values
            assert len(queries) == len(values), f'{len(queries)} {len(values)}'
            for query, value in zip(queries, values):
                query.value = value
            res = queries
        else:
            raise NotImplementedError

        return set(res)


class QueryHandler:
    vk = VKHandler

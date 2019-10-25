from query_object import ComplexQuery, BasicQuery
from collections import defaultdict


# Принимает список базовых запросов. Задача максимально оптимально создать
# составные запросы для наибыстрейшего выполнение всех

class VKHandler:
    service_token_methods = {'friends', 'resolve',
                             'members', 'user_short', 'group_short'}

    user_token_methods = {'groups', 'search',
                          'user_full'}

    methods_group_key = {'user_short', 'user_full',
                         'group_short',
                         'groups'}

    service = 'vk'

    @classmethod
    def combine_queries(cls, methods_dict):
        complex_queries = []
        for method, queries in methods_dict.items():
            if method in cls.methods_group_key:
                keys = [query.key for query in queries]
                query = ComplexQuery(cls.service, method, keys, queries=queries, convert_type=1)
                complex_queries.append(query)
            else:
                complex_queries += [ComplexQuery.from_basic_query(query) for query in queries]

        return complex_queries

    @staticmethod
    def generate_execute_string(queries):
        def query_execute_str(query):
            if query.method == 'friends':
                pass

        assert len(queries) <= 25
        query_strings = [query_execute_str(query) for query in queries]
        code_string = f'return [{",".join(query_strings)}];'
        return code_string

    @classmethod
    def calculate_execute(cls, to_execute):
        size = len(to_execute)
        execute_queries = []
        for i in range(size // 25):
            begin = i * 25
            end = (i + 1) * 25
            if begin < size:
                bunch_queries = to_execute[begin:end]
                execute_string = cls.generate_execute_string(bunch_queries)
                query = ComplexQuery(cls.service, 'execute', execute_string, convert_type=2)
                execute_queries.append(query)

        return execute_queries

    @classmethod
    def get_queries_to_execute(cls, complex_queries):
        return [], complex_queries

    @classmethod
    def encode(cls, queries):
        assert isinstance(queries, list)
        assert len(queries)
        assert isinstance(queries[0], BasicQuery)
        assert not len(cls.methods_group_key -
                       cls.user_token_methods -
                       cls.service_token_methods)

        assert not len(cls.service_token_methods & cls.user_token_methods)

        methods_dict = defaultdict(list)
        for query in queries:
            methods_dict[query.method].append(query)

        complex_queries = cls.combine_queries(methods_dict)
        assert len(complex_queries)
        assert isinstance(complex_queries, list)
        to_execute_queries, other_queries = cls.get_queries_to_execute(complex_queries)
        complex_queries = cls.calculate_execute(to_execute_queries)
        complex_queries += other_queries

        assert len(complex_queries)
        assert isinstance(complex_queries, list)
        cls.complex_queries = list(complex_queries)
        return cls.complex_queries

    @classmethod
    def decode(cls, complex_query):
        assert isinstance(complex_query, ComplexQuery)
        convert_type = complex_query.convert_type
        res = []
        if convert_type == 0:
            query = complex_query.basic_queries[0]
            query.set_value(complex_query.value)
            res = [query]
        elif convert_type == 1 or convert_type == 2:
            queries = complex_query.basic_queries
            values = complex_query.value
            assert isinstance(queries, list)
            assert isinstance(values, list)
            assert len(queries) == len(values)
            for query, value in zip(queries, values):
                query.value = value
            res = values
        else:
            raise NotImplementedError

        return set(res)


class QueryHandler:
    vk = VKHandler


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

    def __init__(self, queries):
        assert isinstance(queries, list)
        assert len(queries)
        assert isinstance(queries[0], BasicQuery)
        assert not len(self.methods_group_key -
                       self.user_token_methods -
                       self.service_token_methods)

        assert not len(self.service_token_methods & self.user_token_methods)

        methods_dict = defaultdict(list)
        for query in queries:
            methods_dict[query.method].append(query)

        complex_queries = set(self.combine_queries(methods_dict))
        assert len(complex_queries)
        assert isinstance(complex_queries, set)
        to_execute_queries = set(self.get_queries_to_execute(complex_queries))
        complex_queries -= to_execute_queries
        complex_queries |= set(self.calculate_execute(to_execute_queries))

        assert len(complex_queries)
        assert isinstance(complex_queries, set)
        self.complex_queries = list(complex_queries)

    def combine_queries(self, methods_dict):
        complex_queries = []
        for method, queries in methods_dict.items():
            if method in self.methods_group_key:
                keys = [query.key for query in queries]
                query = ComplexQuery(self.service, method, keys, queries=queries)
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
                query = ComplexQuery(cls.service, 'execute', execute_string)
                execute_queries.append(query)

        return execute_queries

    @classmethod
    def get_queries_to_execute(cls, complex_queries):
        return []

    def queries(self):
        return self.complex_queries


class QueryHandler:

    @classmethod
    def vk_handler(cls, queries):
        return VKHandler(queries).queries()

    @classmethod
    def ig_handler(cls, queries):
        # {}
        return queries

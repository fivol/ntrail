from query_object import APIQuery
from local_cache import LocalCache
from api_server_call import APIServerCall


class APIQueries:
    def __init__(self):
        self.queries = set()
        self.valid = True
        self.curr_num = 0

    def __add__(self, other):
        for query in other.queries:
            self.add_query(query)
        return self

    def one(self, *args, exe=True, **kwargs):
        self.add_query(APIQuery(*args, **kwargs))
        if exe:
            return self.execute()

    def many(self, service, method, keys, exe=False):
        assert isinstance(service, str)
        assert isinstance(method, str)
        assert isinstance(keys, list)
        if not keys:
            return []
        for key in keys:
            assert isinstance(key, str)
            self.add_query(APIQuery(service, method, key))

        if exe:
            return self.execute()

    def print(self):
        print('Len:', len(self.queries))

    def add_query(self, query):
        assert isinstance(query, APIQuery)
        query.num = self.curr_num
        self.curr_num += 1
        self.queries.add(query)

    @classmethod
    def right_order_queries(cls, queries):
        assert isinstance(queries, set)
        queries = list(queries)
        queries = sorted(queries, key=lambda x: x.num)
        return [query.value for query in queries]

    def execute(self):
        assert self.valid
        self.valid = False
        cached_queries = LocalCache.get_cached_queries_set(queries=self.queries)
        assert isinstance(cached_queries, set)
        unknown_queries = self.queries - cached_queries
        result_queries = APIServerCall(unknown_queries).execute()
        LocalCache.cache_queries_set(result_queries)
        return self.right_order_queries(cached_queries | result_queries)

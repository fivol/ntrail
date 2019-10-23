from query_object import APIQuery
from local_cache import LocalCache
from api_server_call import APIServerCall


class APIQueries:
    def __init__(self):
        self.queries = set()
        self.valid = True

    def print(self):
        print('Len:', len(self.queries))

    def add_query(self, query):
        assert isinstance(query, APIQuery)
        self.queries.add(query)

    @classmethod
    def right_order_answer(cls, queries):
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
        return self.right_order_answer(cached_queries | result_queries)

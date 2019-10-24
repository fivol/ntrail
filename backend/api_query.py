from query_object import BasicQuery
from local_cache import LocalCache
from api_server_call import APIServerCall
from glbal import logger


class APIQueries:
    def __init__(self):
        self.queries = set()
        self.valid = True
        self.curr_num = 0

    def __add__(self, other):
        for query in other.queries:
            self.add_query(query)
        return self

    def one(self, service, method, key, params=None, exe=True):
        self.add_query(BasicQuery(service, method, key, params))
        if exe:
            return self.execute()

    def many(self, service, method, keys, exe=False):
        assert isinstance(service, str)
        assert isinstance(method, str)
        assert isinstance(keys, list)
        for key in keys:
            self.add_query(BasicQuery(service, method, key))

        if exe:
            return self.execute()

    def add_query(self, query):
        assert isinstance(query, BasicQuery)
        query.num = self.curr_num
        self.curr_num += 1
        self.queries.add(query)

    @classmethod
    def right_order_queries(cls, queries):
        assert isinstance(queries, set)
        queries = list(queries)
        queries = sorted(queries, key=lambda x: x.num)
        return [query.value for query in queries]

    @classmethod
    def get_queries_to_cache(cls, queries):
        assert isinstance(queries, set)
        return set([query for query in queries if query.can_cache])

    def execute(self):
        assert self.valid
        self.valid = False
        cached_queries = LocalCache.get_cached_queries_set(queries=self.queries)
        # logger.debug('Find cached queries: %s', len(cached_queries))
        assert isinstance(cached_queries, set)
        unknown_queries = self.queries - cached_queries
        # logger.debug('Find unknown queries: %s %s', len(unknown_queries), unknown_queries)
        if unknown_queries:
            result_queries = APIServerCall(unknown_queries).execute()
            queries_to_cache = self.get_queries_to_cache(result_queries)
            LocalCache.cache_queries_set(queries_to_cache)
            cached_queries |= result_queries

        result = self.right_order_queries(cached_queries)
        assert len(result) == len(self.queries)
        return result

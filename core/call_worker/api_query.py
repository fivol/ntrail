from config import config
from .worker.query_object import BasicQuery
from core.local_cache import LocalCache
from .api_server_call import APIServerCall
from .worker.api_errors import APIError
import typing as t


class APIQueries:
    default_env = {}

    def __init__(self):
        self.queries = set()
        self.valid = True
        self.curr_num = 0

    @classmethod
    def add_default_env(cls, env: dict):
        cls.default_env = {**cls.default_env, **env}

    def __add__(self, other):
        for query in other.queries:
            self.add_query(query)
        return self

    def one(self, service, method, key, params=None, force=False):
        self.add_query(BasicQuery(service, method, key, params=params))
        response = self.execute(force)[0]
        if isinstance(response, APIError):
            raise response
        if not isinstance(response, dict):
            raise Exception('Unknown api response')
        return response

    def many(self, service: str, method: str, keys, force=False):
        assert isinstance(service, str)
        assert isinstance(method, str)
        assert isinstance(keys, list)
        for key in keys:
            self.add_query(BasicQuery(service, method, key))

        if keys:
            return self.execute(force)

    def add_query(self, query: BasicQuery):
        assert isinstance(query, BasicQuery)
        query.env = {**self.default_env, **query.env}
        query.num = self.curr_num
        self.curr_num += 1
        self.queries.add(query)

    @classmethod
    def right_order_queries(cls, queries: t.Set[BasicQuery]):
        assert isinstance(queries, set)
        queries = list(queries)
        assert len(queries) == sorted([query.num for query in queries])[-1] + 1
        queries = sorted(queries, key=lambda x: x.num)
        return [query.value for query in queries]

    @classmethod
    def get_queries_to_cache(cls, queries: t.List[BasicQuery]):
        assert isinstance(queries, set)
        return set([query for query in queries if query.can_cache])

    def execute(self, force):
        assert self.valid
        self.valid = False
        if force:
            cached_queries = set()
        else:
            cached_queries = LocalCache.get_cached_queries_set(queries=self.queries)
        assert isinstance(cached_queries, set)
        unknown_queries = self.queries - cached_queries
        if unknown_queries:
            result_queries = APIServerCall(unknown_queries).execute()
            queries_to_cache = self.get_queries_to_cache(result_queries)
            LocalCache.cache_queries_set(queries_to_cache)
            cached_queries |= result_queries

        result = self.right_order_queries(cached_queries)
        result = [APIError(item) if APIError.is_error(item) else item for item in result]
        assert len(result) == len(self.queries)
        return result

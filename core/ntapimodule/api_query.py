from config import config
from query_object import BasicQuery
from local_cache import LocalCache
from ntapimodule.api_server_call import APIServerCall
from ntapimodule.api_errors import APIError
from flask import g
from auth.db import AuthDB
import typing as t


class APIQueries:
    def __init__(self):
        self.queries = set()
        self.valid = True
        self.curr_num = 0

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
        # Добавление пользовательского токена к запросу
        query.access_token = None
        if hasattr(g, 'user'):
            query.access_token = AuthDB.get_api_token(user_id=g.user.id, service=query.service)
        # TODO Продумать нормально неавторизованные запросы. Сейчас все выполняется от моего имени
        if not query.access_token:
            query.access_token = config.get('MY_VK_ACCESS_TOKEN')
        assert query.access_token
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

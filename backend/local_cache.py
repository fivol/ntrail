from query_object import BasicQuery
from models import QueryModel
import datetime


class LocalCache:

    @staticmethod
    def get_cached_queries_set(queries):
        if not queries:
            return set()
        assert isinstance(queries, set)
        for query in queries:
            assert isinstance(query, BasicQuery)
            assert query.valid

        queries_dict = {query.hash: query for query in queries}
        hashes = list(queries_dict.keys())
        cached_queries = QueryModel.select().where(QueryModel.hash.in_(hashes)).execute()

        saved_queries = set()
        for cached_query in cached_queries:
            queries_dict[cached_query.hash].value = cached_query.value
            saved_queries.add(queries_dict[cached_query.hash])

        return saved_queries.copy()

    @staticmethod
    def cache_queries_set(queries):
        if not queries:
            return
        assert isinstance(queries, set)
        models_list = []
        for query in queries:
            assert isinstance(query, BasicQuery)
            assert query.can_cache
            model = QueryModel(hash=query.hash,
                               service=query.service,
                               method=query.method,
                               key=query.key,
                               value=query.value,
                               params=query.params)
            models_list.append(model)
        QueryModel.bulk_create(models_list)
        # QueryModel.bulk_create(models_list).on_conflict_ignore().execute()

    @classmethod
    def remove_queries_from_time(cls, time):
        QueryModel.delete().where(QueryModel.time >= time).execute()

    @classmethod
    def count_cached_queries(cls):
        return QueryModel.select().count()

from query_object import APIQuery
from models import QueryModel


class LocalCache:

    @staticmethod
    def get_cached_queries_set(queries):
        if not queries:
            return set()
        assert isinstance(queries, list)
        for query in queries:
            assert isinstance(query, APIQuery)
            assert query.valid

        queries_dict = {hash(query): query for query in queries}
        hashes = list(queries_dict.keys())
        cached_queries = QueryModel.select().where(QueryModel.hash.in_(hashes))

        saved_queries = set()
        for cached_query in cached_queries:
            queries_dict[cached_query.hash].result = cached_query.value
            saved_queries.add(queries_dict[cached_query.hash])

        return saved_queries

    @staticmethod
    def cache_queries_set(queries):
        if not queries:
            return
        assert isinstance(queries, set)
        models_list = []
        for query in queries:
            assert isinstance(query, APIQuery)
            assert query.can_cache
            model = QueryModel(service=query.service,
                               method=query.method,
                               key=query.key,
                               value=query.value)
            models_list.append(model)

        QueryModel.bulk_create(models_list)

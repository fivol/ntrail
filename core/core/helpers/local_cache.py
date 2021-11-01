from .call_worker.worker.query_object import BasicQuery
from core.models import QueryModel, db
import datetime
from config import CACHE_TYPE
from core.constants import CACHE_TYPE_ONLY_WRITE, CACHE_TYPE_ONLY_READ, CACHE_TYPE_IGNORE


def local_cache_command(action):
    def cache_pre_process(func):
        def wrapper(*args, **kwargs):
            if CACHE_TYPE == CACHE_TYPE_IGNORE:
                return set()
            if action == 'read' and CACHE_TYPE == CACHE_TYPE_ONLY_WRITE:
                return set()
            if action == 'write' and CACHE_TYPE == CACHE_TYPE_ONLY_READ:
                return set()

            return func(*args, **kwargs)

        return wrapper

    return cache_pre_process


class LocalCache:

    @staticmethod
    @local_cache_command('read')
    def get_cached_queries_set(queries):
        if not queries:
            return set()
        assert isinstance(queries, set)
        for query in queries:
            assert isinstance(query, BasicQuery)
            assert query.valid

        queries_dict = {query.hash: query for query in queries}
        hashes = list(queries_dict.keys())
        cached_queries = QueryModel.select().where(QueryModel.identity_hash.in_(hashes)).execute()

        saved_queries = set()
        for cached_query in cached_queries:
            queries_dict[cached_query.identity_hash].value = cached_query.value
            saved_queries.add(queries_dict[cached_query.identity_hash])

        return saved_queries.copy()

    @staticmethod
    @local_cache_command('write')
    def cache_queries_set(queries):
        if not queries:
            return
        assert isinstance(queries, set)
        with db.atomic():
            for query in queries:
                assert isinstance(query, BasicQuery)
                assert query.can_cache
                QueryModel.insert(identity_hash=query.hash,
                                  service=query.service,
                                  method=query.method,
                                  key=query.key,
                                  value=query.value,
                                  params=query.params).on_conflict(
                    conflict_target=[QueryModel.identity_hash],
                    preserve=[QueryModel.value]
                ).execute()

    @classmethod
    def remove_queries_from_time(cls, time):
        assert isinstance(time, datetime.datetime), type(time)
        QueryModel.delete().where(QueryModel.time >= time).execute()

    @classmethod
    def count_cached_queries(cls):
        return QueryModel.select().count()

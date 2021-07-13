from collections import defaultdict
from .modules.vk.vk import VKAPI
from .modules.instagram.instagram import IGAPI
from .query_handler import QueryHandler
from .query_object import BasicQuery, ComplexQuery
from .config import logger
from .api_errors import ServerError

import requests


def internet_on():
    """Return True if internet on (can ping google.com)"""
    check_internet_url = 'https://google.com'
    try:
        requests.get(check_internet_url, timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        return False


api_dict = {'vk': VKAPI, 'instagram': IGAPI}


class APIServerEmulator:
    """
        Заменяет сервер, обрабатывающий и распределяющий входящие апи запросы
        Нужен для теста в пределах одного скрипта
    """

    @classmethod
    def extract_query_objects(cls, request_json):
        assert isinstance(request_json, dict)
        version = request_json['version']

        if version == 0:
            queries = request_json['queries']
            return [BasicQuery.from_dict(query) for query in queries]
        else:
            raise NotImplementedError

    @classmethod
    def encode_complex_queries(cls, basic_queries):
        # Самый простой вариант. Не группируем запросы, а передаем в исходном виде
        complex_queries = []
        assert isinstance(basic_queries, set)
        service_dict = defaultdict(list)
        for query in basic_queries:
            service_dict[query.service].append(query)

        for service, queries in service_dict.items():
            if hasattr(QueryHandler, service):
                complex_queries += getattr(QueryHandler, service).encode(queries=queries)
            else:
                complex_queries += [ComplexQuery.from_basic_query(query) for query in queries]

        return set(complex_queries)

    @classmethod
    def decode_complex_queries(cls, complex_queries):
        basic_queries = set()
        for query in complex_queries:
            service = query.service
            if hasattr(QueryHandler, service):
                basic_queries |= getattr(QueryHandler, service).decode(query)
            else:
                basic_queries.add(query)

        return basic_queries

    @classmethod
    def run_query(cls, query: ComplexQuery):
        assert isinstance(query, ComplexQuery)
        params = query.params
        if params is None:
            params = {}

        # Создаем api_remote класс
        # Инизиализируем с помощью токена пользователя
        # От имени которого совершаются запросы
        api_class = api_dict[query.service]
        print(query.to_dict())
        api_class_instance = api_class(access_token=query.access_token)
        method = query.method

        assert isinstance(method, str)
        assert hasattr(api_class_instance, method)

        try:
            res = getattr(api_class_instance, method)(query.key, **params)
            if isinstance(res, dict):
                res['status'] = res.get('status', 'ok')
            logger.debug('* Request %s %s', method, query.key)
        except Exception as e:
            assert internet_on(), 'NO INTERNET'

            if isinstance(e, AssertionError):
                raise e
            logger.exception('Fail to execute api method: %s', query.to_dict())
            res = ServerError(0)

        query.set_value(res)

    @classmethod
    def run_complex_queries(cls, complex_queries):
        assert len(complex_queries)
        assert isinstance(next(iter(complex_queries)), ComplexQuery)
        for query in complex_queries:
            cls.run_query(query)

        return complex_queries

    @classmethod
    def order_by_hashes(cls, query_objects, hashes_list):
        assert isinstance(hashes_list, list)
        assert isinstance(query_objects, set)
        queries_dict = {query.hash: query for query in query_objects}
        return [queries_dict[h] for h in hashes_list]

    @classmethod
    def execute(cls, request_json):
        # Это просто для проверки работоспособности системы.
        # TODO Тут должно быть реализовано декодирование запросов
        # группировка по сервису, группировка по объему типу и отправка нужному серверу (в данном случае классу)
        basic_query_objects = cls.extract_query_objects(request_json)

        assert isinstance(basic_query_objects, list)
        assert len(basic_query_objects)
        assert isinstance(basic_query_objects[0], BasicQuery)

        queries_hashes = [query.hash for query in basic_query_objects]

        complex_queries = cls.encode_complex_queries(set(basic_query_objects))

        assert isinstance(complex_queries, set)
        assert len(complex_queries)
        assert isinstance(next(iter(complex_queries)), ComplexQuery)

        executed_queries = cls.run_complex_queries(complex_queries)

        assert isinstance(executed_queries, set)
        assert len(executed_queries)
        assert len(executed_queries) == len(complex_queries)
        assert isinstance(next(iter(executed_queries)), ComplexQuery)

        basic_query_results = cls.decode_complex_queries(executed_queries)

        assert isinstance(basic_query_objects, list)
        assert len(basic_query_results) == len(set(basic_query_objects))
        assert isinstance(next(iter(basic_query_results)), BasicQuery)

        basic_queries = cls.order_by_hashes(basic_query_results, queries_hashes)
        return [query.value for query in basic_queries]

from api_server.vkapi_remote import VKAPI
from api_server.igapi_remote import IGAPI
from api_server.query_handler import QueryHandler
from query_object import BasicQuery, ComplexQuery
from glbal import logger
from constants import QUERY_RESULT_ERROR
from collections import defaultdict

api_dict = {'vk': VKAPI, 'ig': IGAPI}


# Заменяет сервер, обрабатывающий и распределяющий входящие апи запросы
# Нужен для теста в пределах одного скрипта
class APIServerEmulator:

    @classmethod
    def extract_query_objects(cls, request_json):
        # {}
        assert isinstance(request_json, dict)
        version = request_json['version']

        if version == 0:
            queries = request_json['queries']
            return [BasicQuery.from_dict(query) for query in queries]
        else:
            raise NotImplementedError

    @classmethod
    def generate_complex_queries(cls, basic_queries):
        # {}
        # Самый простой вариант. Не группируем запросы, а передаем в исходном виде
        complex_queries = []
        assert isinstance(basic_queries, list)
        service_dict = defaultdict(list)
        for query in basic_queries:
            service_dict[query.service].append(query)

        for service, queries in service_dict.items():
            service_handler_name = f'{service}_handler'
            if hasattr(QueryHandler, service_handler_name):
                complex_queries += getattr(QueryHandler, service_handler_name)(queries=queries)
            else:
                complex_queries += [ComplexQuery.from_basic_query(query) for query in queries]

        return complex_queries

    @classmethod
    def run_complex_queries(cls, complex_queries):
        # {}
        assert len(complex_queries)
        assert isinstance(complex_queries[0], ComplexQuery)
        for request in complex_queries:
            params = request.params
            if params is None:
                params = {}

            api_class = api_dict[request.service]
            method = request.method

            if hasattr(api_class, method):
                try:
                    res = getattr(api_class, method)(request.key, **params)
                except:
                    logger.exception('Fail to execute api method: %s', request.to_dict())
                    res = QUERY_RESULT_ERROR

                request.set_value(res)
            else:
                raise NotImplementedError

        return complex_queries

    @classmethod
    def order_by_hashes(cls, query_objects, hashes_list):
        queries_dict = {query.hash: query for query in query_objects}
        return [queries_dict[h] for h in hashes_list]

    @classmethod
    def execute(cls, request_json):
        # Это просто для проверки работоспособности системы. Тут должно быть релизовано декадирование запросов
        # группировка по сервису, группировка по объему типу и отправка нужному серверу (в данном случае классу)
        basic_query_objects = cls.extract_query_objects(request_json)

        assert isinstance(basic_query_objects, list)
        assert len(basic_query_objects)
        assert isinstance(basic_query_objects[0], BasicQuery)

        queries_hashes = [query.hash for query in basic_query_objects]
        complex_queries = cls.generate_complex_queries(basic_query_objects)

        assert isinstance(complex_queries, list)
        assert len(complex_queries)
        assert isinstance(complex_queries[0], ComplexQuery)

        executed_queries = cls.run_complex_queries(complex_queries)

        assert isinstance(executed_queries, list)
        assert len(executed_queries) == len(complex_queries)
        assert isinstance(executed_queries[0], ComplexQuery)

        basic_query_results = [list(query.split_basic_queries()) for query in executed_queries]
        basic_query_results = sum(basic_query_results, [])

        assert len(basic_query_results) == len(basic_query_objects)

        basic_queries = cls.order_by_hashes(basic_query_results, queries_hashes)
        return [query.value for query in basic_queries]

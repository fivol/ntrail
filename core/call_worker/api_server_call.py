from core.call_worker.worker.query_object import BasicQuery
from core.call_worker.worker.api_server import APIServerEmulator
from config import API_SERVER_REQUEST_VERSION


class APIServerCall:

    def __init__(self, queries):
        assert isinstance(queries, set)
        for query in queries:
            assert isinstance(query, BasicQuery)

        self.queries_list = sorted(list(queries), key=lambda x: x.num)
        self.queries = queries

    @staticmethod
    def generate_request_json(queries):
        assert isinstance(queries, list)
        version = API_SERVER_REQUEST_VERSION
        request_json = {
            'version': version
        }

        if version == 0:
            request_json['queries'] = [query.to_dict() for query in queries]
        else:
            raise NotImplementedError()

        # Временное решение. Надо будет сделать нормально. Оптимально, эффективно по объему данных
        return request_json

    @staticmethod
    def call_api_server(request_json):
        # Тут должен быть вызов сетевого интерфейса (например requests.post) с необходимой обработкой
        return APIServerEmulator().execute(request_json)

    def execute(self):
        request_json = self.generate_request_json(self.queries_list)
        assert len(request_json)
        assert isinstance(request_json, dict) or isinstance(request_json, list) or isinstance(request_json, str)
        answer = self.call_api_server(request_json)

        assert isinstance(answer, list)
        assert len(answer) == len(self.queries), len(answer)
        for query, res in zip(self.queries_list, answer):
            query.set_value(res)

        return self.queries

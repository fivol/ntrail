from query_object import APIQuery
from api_server import APIServerEmulator


class APIServerCall:

    def __init__(self, queries):
        assert isinstance(queries, set)
        for query in queries:
            assert isinstance(query, APIQuery)

        self.queries_list = sorted(list(queries), key=lambda x: x.num)
        self.queries = queries

    @staticmethod
    def generate_request_json(queries):
        assert isinstance(queries, list)
        # Временное решение. Надо будет сделать нормально. Оптимально, эффективно по объему данных
        return [query.to_dict() for query in queries]

    @staticmethod
    def call_api_server(request_json):
        # Тут должен быть вызов сетевого интерфейса (например requests.post) с необходимой обработкой
        return APIServerEmulator().incoming_request(request_json)

    def execute(self):
        request_json = self.generate_request_json(self.queries_list)
        assert request_json
        assert isinstance(request_json, dict) or isinstance(request_json, list) or isinstance(request_json, str)
        answer = self.call_api_server(request_json)

        assert isinstance(answer, list)
        assert len(answer) == len(self.queries)
        for query, res in zip(self.queries, answer):
            query.set_value(res)

        return self.queries

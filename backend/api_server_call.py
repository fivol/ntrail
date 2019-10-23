from models import QueryModel
from query_object import APIQuery


class APIServerCall:

    def __init__(self, queries):
        assert isinstance(queries, list)
        for query in queries:
            assert isinstance(query, APIQuery)

        self.queries = queries

    @staticmethod
    def generate_request_json(queries):
        pass

    def call_api_server(self, request_json):
        pass

    def execute(self):
        request_json = self.generate_request_json(self.queries)
        assert request_json
        assert isinstance(request_json, dict) or isinstance(request_json, list) or isinstance(request_json, str)
        answer = self.call_api_server(request_json)

        assert isinstance(answer, list)
        assert len(answer) == len(self.queries)
        return answer
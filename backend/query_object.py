import hashlib
from constants import QUERY_RESULT_ERROR


class BasicQuery:
    def __init__(self, service, method, key, num=-1, params=None):
        if params is None:
            params = dict()
        if isinstance(key, int):
            key = str(key)
        assert isinstance(params, dict)
        assert isinstance(service, str)
        assert isinstance(method, str)
        assert isinstance(key, str)
        self.service = service
        self.method = method
        self.key = key
        self.num = num
        self.params = params
        self.value = None

    def set_value(self, value):
        self.value = value

    def __repr__(self):
        return f'{self.service} {self.method} {self.key}'

    def __hash__(self):
        s = self.service + self.method + self.key + str(sorted(self.params.items()))
        return hash(s)

    @property
    def hash(self):
        s = self.service + self.method + self.key + str(sorted(self.params.items()))
        h = hashlib.md5(s.encode()).hexdigest()[:20]
        return h

    @property
    def valid(self):
        if not self.service:
            return False
        if not self.method:
            return False
        if not self.key:
            return False
        return True

    def to_dict(self):
        assert self.valid
        return {
            'service': self.service,
            'method': self.method,
            'key': self.key,
            'value': self.value,
            'params': self.params
        }

    @classmethod
    def from_dict(cls, obj_dict):
        assert isinstance(obj_dict, dict)
        return BasicQuery(obj_dict['service'], obj_dict['method'], obj_dict['key'], params=obj_dict['params'])

    @property
    def can_cache(self):
        return self.valid and not (self.value is None) and not(self.value == QUERY_RESULT_ERROR)


class ComplexQuery(BasicQuery):
    def __init__(self, service, method, key, queries=None, **kwargs):
        self.basic_queries = set()
        if isinstance(key, list):
            key = str(list)
        if queries:
            assert isinstance(queries, set)
            self.basic_queries |= queries
        super().__init__(service, method, key, **kwargs)

    @classmethod
    def from_basic_query(cls, query):
        return ComplexQuery(query.service, query.method, query.key, params=query.params)

    def split_basic_queries(self):
        assert self.can_cache
        return self.basic_queries

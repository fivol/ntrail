import hashlib
from .api_errors import APIError


class BasicQuery:
    def __init__(self, service: str, method: str, key, num: int = -1, params=None, env: dict = None, **kwargs):
        """
        :access_token: токен доступа к сервису
        TODO заменить access_token на объект идентификации, включающий в себя id пользователя и access_token
        """
        if params is None:
            params = dict()

        assert isinstance(params, dict)
        assert isinstance(service, str)
        assert isinstance(method, str)
        self.service = service
        self.method = method
        self.env = env or {}
        self.key = key
        self.num = num
        self.params = params
        self.value = kwargs.get('value')

    def set_value(self, value):
        self.value = value

    def __repr__(self):
        return f'{self.service} {self.method} {self.key} {self.params}'

    def __hash__(self):
        s = self.service + self.method + str(self.key) + str(sorted(self.params.items()))
        return hash(s)

    @property
    def hash(self):
        s = self.service + self.method + str(self.key) + str(sorted(self.params.items()))
        h = hashlib.md5(s.encode()).hexdigest()[:16]
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
            'params': self.params,
            'env': self.env
        }

    @classmethod
    def from_dict(cls, obj_dict):
        assert isinstance(obj_dict, dict)
        return BasicQuery(**obj_dict)

    @property
    def can_cache(self):
        if self.value is None:
            return False
        if APIError.is_error(self.value):
            if not APIError(self.value).is_request_result():
                return False

        return self.valid


class ComplexQuery(BasicQuery):
    def __init__(self, service, method, key, queries=None, params=None, convert_type=0, env: dict = None, **kwargs):
        self.basic_queries = queries
        self.convert_type = convert_type
        assert len(queries)
        assert isinstance(queries, list)
        self.env = env or {}
        # Добавление access_token из queries
        if queries and len(queries):
            first_query: BasicQuery = next(iter(queries))
            self.env = first_query.env

        if convert_type == 0:
            assert len(queries) == 1
            assert isinstance(key, str)
        elif convert_type == 1:
            assert len(queries)
            assert isinstance(key, list)
        elif convert_type == 2:
            assert len(queries)
        else:
            raise NotImplementedError

        super().__init__(service, method, key, params=params, env=env, **kwargs)

    @classmethod
    def from_basic_query(cls, query: BasicQuery):
        return ComplexQuery(query.service, query.method, query.key,
                            queries=[query], params=query.params, convert_type=0)

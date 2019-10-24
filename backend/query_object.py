class APIQuery:
    def __init__(self, service, method, key, num=-1, params=None):
        if params is None:
            params = dict()
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

    def __hash__(self):
        return hash(self.service + self.method + self.key + str(sorted(self.params.items())))

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

    @property
    def can_cache(self):
        return self.valid and not (self.value is None)

class APIQuery:
    def __init__(self):
        self.service = None
        self.method = None
        self.key = None
        self.num = None
        self.value = None

    def __hash__(self):
        return hash(self.service + self.method + self.key)

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
            'value': self.value
        }

    @property
    def can_cache(self):
        return self.valid and not (self.value is None)

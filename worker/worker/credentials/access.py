class AccessModel:
    def __init__(self, row):
        self.data = row['data']
        self.token = row['token']
        self._row = row

    def row(self):
        return self._row

    def __hash__(self):
        return self._row['id']

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __lt__(self, other):
        return hash(self) < hash(other)

    def __repr__(self):
        return f'AccessModel({dict(self._row)})'


if __name__ == '__main__':
    print({AccessModel({'id': 2, 'type': 'app', 'data': {},
                        'token': '2c575b732c575b732c575b73b62c3822f022c572c575b7372603a3335071351c65615ca',
                        'service': 'vk'}),
           AccessModel({'id': 2, 'type': 'app', 'data': {},
                        'token': '2c575b732c575b732c575b73b62c3822f022c572c575b7372603a3335071351c65615ca',
                        'service': 'vk'})})

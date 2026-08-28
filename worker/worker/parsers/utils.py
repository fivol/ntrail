class RichList(list):
    count_ = 0
    data = {}

    def __add__(self, other):
        result = RichList(super().__add__(other))
        result.count_ = max(self.count_, getattr(other, 'count_', 0))
        result.data = {**self.data, **other.data}
        return result


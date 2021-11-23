class ListWithCount(list):
    count_ = None

    def __add__(self, other):
        result = ListWithCount(super().__add__(other))
        result.count_ = self.count_ or getattr(other, 'count_')
        return result

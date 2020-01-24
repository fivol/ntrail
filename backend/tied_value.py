

class TiedValue:
    def __init__(self, value_, id_):
        self.value = value_
        self.id = id_

    def __add__(self, other):
        assert isinstance(self.value, list), self.value
        assert isinstance(other, list), other
        return [TiedValue(item, self.id) for item in self.value] + other

    def __sub__(self, other):
        return TiedValue(self.value - other, self.id)

    def __neg__(self):
        return TiedValue(-self.value, self.id)

    def __truediv__(self, other):
        return TiedValue(self.value / other, self.id)

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, name):
        return TiedValue(self.value[name], self.id)

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self.value)

    def __bool__(self):
        return bool(self.value)

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

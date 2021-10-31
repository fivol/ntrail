import re

from core.module.frontend_preparing import is_number


class TiedValue:
    def __init__(self, value_, id_):
        self.value = value_
        self.id = id_

    def get_value(self):
        return self.value

    def with_value(self, new_value):
        return TiedValue(new_value, self.id)

    def split(self):
        return [TiedValue(word, self.id) for word in self.value.split()]

    def lower(self):
        return self.with_value(self.value.lower())

    def sub(self, source, target):
        return self.with_value(re.sub(source, target, self.value))

    def capitalize(self):
        return self.with_value(self.value.capitalize())

    def to_dict(self, round_digits=None):
        if round_digits is not None and is_number(self.value):
            return {
                'value': round(self.value, round_digits),
                'id': self.id
            }
        return {
            'value': self.value,
            'ids': self.get_ids()
        }

    def get_ids(self, prefix=None):
        if isinstance(self.id, list):
            ids = self.id
        else:
            ids = [self.id]
        if prefix:
            ids = [f'{prefix}{id_}' for id_ in ids]
        return ids

    def __add__(self, other):
        if isinstance(other, list):
            return [TiedValue(item, self.id) for item in self.value] + other
        return TiedValue(self.value + other, self.id)

    def __sub__(self, other):
        return TiedValue(self.value - other, self.id)

    def __len__(self):
        return len(self.value)

    def __neg__(self):
        return TiedValue(-self.value, self.id)

    def __truediv__(self, other):
        return TiedValue(self.value / other, self.id)

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, name):
        return TiedValue(self.value[name], self.id)

    def __repr__(self):
        return f'TiedValue({self.value}, {self.id})'

    def __hash__(self):
        return hash(self.value)

    def __bool__(self):
        return bool(self.value)

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        if isinstance(other, TiedValue):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value


def get_tied_array_size(arr):
    return TiedValue(len(arr), sum([item.get_ids() for item in arr], []))


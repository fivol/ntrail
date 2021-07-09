from collections import defaultdict

from ntmodule.tied_value import TiedValue


class TiedCounter:
    def __init__(self, arr):
        if isinstance(arr, dict):
            self.counter = arr
            return

        if len(arr):
            assert isinstance(arr[0], TiedValue)

        self.size = TiedValue(len(arr), sum([item.get_ids() for item in arr], []))
        values_dict = defaultdict(list)
        for item in arr:
            values_dict[item.value] += item.get_ids()
        self.counter = values_dict

    def __add__(self, other):
        assert isinstance(other, TiedCounter)
        return TiedCounter({**self.counter, **other.counter})

    def most_common(self, count=None, ignore_single=False, min_count=3):
        res = sorted(
            [
                (TiedValue(value, ids), len(ids))
                for value, ids in self.counter.items()
            ],
            key=lambda x: x[1],
            reverse=True
        )

        if count:
            res = res[:count]
        if ignore_single:
            res_without_single = [(value, count) for value, count in res if count > 1]

            if len(res_without_single) < min_count:
                res = res[:min_count]
            else:
                res = res_without_single

        return res

    def __getitem__(self, key):
        return TiedValue(len(self.counter[key]), self.counter[key])

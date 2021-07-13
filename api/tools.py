from jsonpath_ng import jsonpath, parse


class SmartAccessDict(dict):
    # JSON Path lib https://pypi.org/project/jsonpath-ng/
    def get(self, key, default=None):
        jsonpath_expr = parse(key)
        iterator = iter(jsonpath_expr.find(dict(self)))
        try:
            return next(iterator).value or default
        except StopIteration:
            return default



if __name__ == '__main__':
    a = SmartAccessDict({'a': {'b': 123, 'd': 'hello'}, 'x': [0, 3, 4]})
    assert a.get('a.b') == 123
    assert a.get('a.k') is None
    assert a.get('a.d') == 'hello'
    assert a.get('x[1]') == 3
    assert a.get('unknown') is None
    assert a.get('unknown', 34) == 34
    assert a.get('unknown.asdf.asdf[1]', 34) == 34

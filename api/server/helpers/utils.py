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


def get_value_by_path(data, full_path):
    path_elements = full_path.split('.')
    obj = data
    for key in path_elements:
        obj = obj[key]
    return obj


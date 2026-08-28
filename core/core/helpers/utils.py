from functools import wraps


def dicts_keys(dicts):
    keys = set()
    for d in dicts:
        keys.update(set(d))
    return list(keys)


def counter_top(common_list, break_point=1):
    return [(item, count) for item, count in common_list if count > break_point]


def clear_list(list_obj, unique=True):
    return list(set([i for i in list_obj if i]))


def name_to_gent(name):
    if not name:
        logger.warning('Name type: {}, {} in name_to_gent', type(name), name)
        return str(name)
    word = morph.parse(name)[0]
    try:
        return word.inflect({'gent'}).word.capitalize()
    except:
        return name.capitalize()


def file_extension(filename):
    guess_format = filename.split('.')[-1]
    if len(guess_format) < 5 and guess_format != filename:
        return guess_format
    return None


def init_with_result(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        result = await method(self, *args, **kwargs)
        init_object_props(self, result)
        return result

    return wrapper


def init_object_props(self, props):
    for key, value in props.items():
        if key.startswith('_'):
            continue
        if hasattr(self, key) and getattr(self, key) is None:
            setattr(self, key, value)

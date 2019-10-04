import random
from collections import Counter
from time import time
import numpy as np
import re
from functools import reduce
import pickle
from glbal import logger

colors = []

colors += ['#FFFF00', '#0000FF', '#FF0000', '#00FF00', '#FF00FF', '#808000', '#00FFFF', '#800000',
           '#800080']
colors = list(set(colors))
random.shuffle(colors)

objects = {}
stored_data = {}


def load_memory():
    try:
        with open('data/data', 'rb') as f:
            global stored_data
            stored_data = pickle.load(f.read())
    except FileNotFoundError:
        logger.warning('Memory file not found!')


def save_memory():
    try:
        with open('data/data', 'wb') as f:
            pickle.dump(stored_data, f)
    except:
        logger.exception('Fail to save memory')


def once_property(func):
    @property
    def wrapper(class_obj):
        func_name = func.__name__
        class_value_name = f'{func_name}_'
        if hasattr(class_obj, class_value_name):
            return getattr(class_obj, class_value_name)
        method_result = func(class_obj)
        setattr(class_obj, class_value_name, method_result)
        return method_result

    return wrapper


def self_replace(*arg_names):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # print(func.__name__, kwargs)
            for arg_name in arg_names:
                if arg_name not in kwargs:
                    obj = getattr(self, arg_name)
                    if callable(obj):
                        obj = obj()
                    kwargs[arg_name] = obj

            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def timeit(func):
    def wrapper(*args, **kwargs):
        t = time()
        result = func(*args, **kwargs)
        eps = time() - t
        print(f'# timeit {func.__name__} {eps:.5f} {str(time())[8:]}')
        return result
    return wrapper


class Tools:
    @staticmethod
    def reset_colors():
        random.shuffle(colors)

    @classmethod
    def get_obj(cls, id):
        return objects.get(id, None)

    @classmethod
    def get_objs(cls, ids):
        return reduce((lambda x, y: x + y), [Tools.get_obj(id) for id in ids])

    @classmethod
    def set_obj(cls, id, obj):
        objects[id] = obj

    @staticmethod
    def get_color(i, size=None):
        if size == 1:
            return '#000000'
        if i == 0:
            return '#000000'
        if i - 1 >= len(colors):
            return '#FFFFFF'

        return colors[i - 1]

    @classmethod
    def dict_from_dicts(cls, list_obj, key):
        return dict([(item[key], item) for item in list_obj])

    @staticmethod
    def sizeof(obj, mb_capacity=False):
        string = str(obj)
        obj_str_len = len(string.replace(' ', ''))
        size = obj_str_len * 2 / 1024
        if mb_capacity:
            return int(1024 / size)
        return size

    @classmethod
    def list_from_dicts(cls, dicts_list, key, counter=False, ignore_zero=False, most_common=True):
        dicts_list = filter(lambda x: key in x, dicts_list)
        result = map(lambda x: x[key], dicts_list)
        if ignore_zero:
            result = filter(lambda x: bool(x), result)
        if counter:
            res = Counter(result)
            if most_common:
                return res.most_common()
            return res
        return list(result)

    @staticmethod
    def prepare_list(list_object, name, funcs=None, mean=True, median=True,
                     max=True, min=True, count=True, fourth=True, last_fourth=True, clean=False):
        res = {}
        l = np.array(list_object)
        if clean:
            l = l[l != 0]
        if not len(l):
            return {}
        if funcs:
            mean = 'mean' in funcs
            median = 'median' in funcs
            max = 'max' in funcs
            min = 'min' in funcs
            count = 'count' in funcs
            fourth = 'fourth' in funcs
            last_fourth = 'last_fourth' in funcs

        name += '_'
        ordered_list = sorted(l, reverse=True)
        if mean: res[name + 'mean'] = np.mean(l)
        if median: res[name + 'median'] = np.median(l)
        if max: res[name + 'max'] = np.max(l)
        if min: res[name + 'min'] = np.min(l)
        if count: res[name + 'count'] = len(l)
        if fourth: res[name + 'fourth'] = ordered_list[int(len(l) / 4)]
        if last_fourth: res[name + 'last_fourth'] = ordered_list[int(len(l) / 4 * 3)]

        return res

    @staticmethod
    def counter_top(common_list, break_point=1):
        return [(item, count) for item, count in common_list if count > break_point]

    @staticmethod
    def list_get(tuple_list, key):
        return [
            item[1]
            for item in tuple_list
            if item[0] == key
        ]

    @staticmethod
    def get_sites(site_string):
        regex = r'('
        regex += r'(?:(?:https|http):\/\/)?'
        regex += r'(?:www\.)?'
        regex += r'(?:(?:[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\.)+)'
        regex += r'(?:[a-z]{2,6})'
        regex += r'(?:(?:\/[a-z0-9_\-.]+)*)'
        regex += r'(?:\?[^;\s]+)?'
        regex += r')'
        urls = re.findall(regex, site_string)

        sites = []
        for inst_username in re.findall(r'@([a-zA-Z0-9_\.]+)', site_string):
            sites.append(('instagram', 'https://www.instagram.com/{}/'.format(inst_username)))

        for site in urls:
            if site.startswith('www') and len(site.split('.')) <= 2:
                continue
            if not site.startswith('http'):
                site = 'https://' + site

            host = site.split('//')[1]
            if host.startswith('www.'):
                host = host[4:]

            host_name = host.split('/')[0].split('.')[-2]

            sites.append((host_name, site))

        return sites


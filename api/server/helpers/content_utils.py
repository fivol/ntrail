

import difflib
import logging
import math
import pickle
import random
import numpy as np
import re
import string
from collections import Counter
from functools import reduce, wraps
from threading import Thread
from time import time, sleep

import pymorphy2
import transliterate

from core.data import most_frequent_english_words, most_frequent_russian_words, extra_ignore_words
from server.helpers.tied_counter import TiedCounter
from server.helpers.tied_value import TiedValue

logger = logging.getLogger('tools')

morph = pymorphy2.MorphAnalyzer()

most_frequent_words = set('абвгдежзийклмнопстуфхцчшщъыьэюяё') | \
                      set(most_frequent_english_words) | \
                      set(most_frequent_russian_words) | \
                      set(string.ascii_lowercase) | set(extra_ignore_words)

colors = []

colors += ['#FFFF00', '#0000FF', '#FF0000', '#00FF00', '#FF00FF', '#808000', '#00FFFF', '#800000',
           '#800080']
colors = list(set(colors))
random.shuffle(colors)

objects = {}
execution_locked_func = {}


def get_random_color():
    def rand(x, y):
        return random.randint(x, y)

    return '#%02X%02X%02X' % (rand(0, 255), rand(0, 20), rand(100, 255))


def bool_filter(value):
    return [item for item in value if bool(item)]


def once_property(func):
    @property
    @wraps(func)
    def wrapper(class_obj):
        func_name = func.__name__
        class_value_name = f'{func_name}_'
        if hasattr(class_obj, class_value_name):
            return getattr(class_obj, class_value_name)
        method_result = func(class_obj)
        setattr(class_obj, class_value_name, method_result)
        return method_result

    return wrapper


def memorize(func):
    def wrapper(class_obj, *args, **kwargs):
        func_name = func.__name__
        class_value_name = f'{func_name}_'
        if hasattr(class_obj, class_value_name):
            return getattr(class_obj, class_value_name)
        method_result = func(class_obj, *args, **kwargs)
        setattr(class_obj, class_value_name, method_result)
        return method_result

    return wrapper


def self_replace(*arg_names):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for arg_name in arg_names:
                if arg_name not in kwargs:
                    obj = getattr(self, arg_name)
                    if callable(obj):
                        obj = obj()
                    kwargs[arg_name] = obj

            return func(self, *args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def timeit(func):
    def wrapper(*args, **kwargs):
        t = time()
        result = func(*args, **kwargs)
        eps = time() - t
        return result

    return wrapper


def get_color(i, size=None):
    if size == 1:
        return '#000000'
    if i == 0:
        return '#000000'
    if i - 1 >= len(colors):
        return '#FFFFFF'

    return colors[i - 1]


def dict_from_dicts(list_obj, key):
    assert isinstance(list_obj, list)
    return dict([(item[key], item) for item in list_obj if key in item])


def sizeof(obj, mb_capacity=False):
    str_obj = str(obj)
    obj_str_len = len(str_obj.replace(' ', ''))
    size = obj_str_len * 2 / 1024
    if mb_capacity:
        return int(1024 / size)
    return size


def get_field_values(data_list, field, capitalize=False, clean=False, counter=False, key=None):
    def prepare_value(value):
        if key:
            value = value[key]
        if capitalize:
            return value.capitalize()
        return value

    res = [
        TiedValue(prepare_value(user[field]), user['id'])
        for user in data_list
        if field in user
    ]
    if clean:
        res = list(filter(lambda x: bool(x), res))
    if counter:
        return TiedCounter(res)

    return res


class MemoryCache:
    stored_data = {}
    last_save_time = 0
    get_data_locked = False

    @classmethod
    def get(cls, name, save=False):
        while cls.get_data_locked:
            sleep(0.05)
        if time() - cls.last_save_time > 3 or save:
            cls.save_memory()
        default = {}
        if name not in cls.stored_data:
            # logger.warning('ITEM %s not in stored_data', name)
            cls.stored_data[name] = default

        return cls.stored_data[name]

    @classmethod
    def save_memory(cls):
        cls.get_data_locked = True
        try:
            with open('.cache', 'wb') as f:
                pickle.dump(cls.stored_data, f)
        except:
            logger.exception('Fail to save memory')

        cls.last_save_time = time()
        cls.get_data_locked = False

    @classmethod
    def load_memory(cls):
        import pickle
        try:
            with open('.cache', 'rb') as f:
                cls.stored_data = pickle.load(f)
        except FileNotFoundError:
            logger.warning('Memory file not found!')
            cls.save_memory()

    @classmethod
    def clear_memory(cls):
        cls.stored_data.clear()
        cls.save_memory()


def reset_colors():
    random.shuffle(colors)


def get_obj(id):
    return objects.get(id, None)


def get_objs(ids):
    return reduce((lambda x, y: x + y), [get_obj(id) for id in ids])


def set_obj(id, obj):
    objects[id] = obj


def get(name, save=False):
    return MemoryCache.get(name, save)


def list_from_dicts(dicts_list, key, counter=False, ignore_zero=False, most_common=True, capitalize=False):
    dicts_list = filter(lambda x: key in x, dicts_list)
    result = [x[key] for x in dicts_list]
    if ignore_zero:
        result = filter(lambda x: bool(x), result)

    if capitalize:
        result = [item.capitalize() for item in result]
    if counter:
        res = Counter(result)
        if most_common:
            return res.most_common()
        return res
    return list(result)


def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value, in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple([make_json_serializable(item) for item in obj])
    if obj is None:
        return obj

    try:
        if float(obj) == int(obj):
            return int(obj)
        return float(obj)
    except:
        if not isinstance(obj, str):
            logger.warning('Strange object type in json %s %s', type(obj), obj)
        return str(obj)


def merge_lists(lists):
    return sum(lists, [])


def calculate_array_common(arr):
    size = len(arr)
    arr = sorted(arr)
    if not size:
        return []

    gap = min(4, max(2, size // 2))
    common_elements = []
    while gap < size:
        diffs = []
        for i in range(size - gap):
            diff = arr[i + gap] - arr[i]
            diffs.append((diff, i + gap // 2, (arr[i] + arr[i + gap]) / 2))
        best = min(diffs)
        common_elements.append(arr[best[1]])
        gap += gap // 2
    return np.array(common_elements)


def is_good_username(username):
    if len(username) < 2:
        return False
    bad_characters = re.sub('[a-zA-Z0-9_\-.]', '', username)
    if bad_characters == '':
        return True
    # logger.debug('Find bad username: %s', username)
    return False


def find_phones(phones_string):
    phones_string = phones_string.replace(' ', '')
    exp = r'\+?(?:(?:[0-9]{1,3}\([0-9]{3}\))|(?:[0-9]{4,6}))[0-9]{7}'
    return list(re.findall(exp, phones_string))


def get_normal_phone_number(phone_string):
    if len(phone_string) > 20:
        return None
    numbers = re.sub('[^0-9]', '', phone_string)
    if len(numbers) == 11 and numbers[0] == '8':
        numbers = '7' + numbers[1:]

    if len(numbers) == 10:
        numbers = '7' + numbers

    if len(numbers) < 11:
        return None

    phone_code = numbers[:-10]
    if len(phone_code) > 3:
        return None

    phone = '+' + numbers
    return phone


def prepare_list(list_object, mean=True, median=True, fourth=True,
                 max=True, min=True, common=True, count=True, clean=False):
    res = {}
    l = sorted(list_object)
    basic_list = [item.value for item in l]
    if clean:
        l = [item for item in l if item != 0]
    if not len(l):
        return {
            'count': 0,
            # 'list': [],
            # 'max': None,
            # 'min': None,
            # 'median': None,
            # 'common_mean': None,
            # 'common_median': None,
            # 'fourth': None,
            # 'fourth2': None
        }
    # res['list'] = list(list_object)[::-1]
    if mean: res['mean'] = sum(basic_list) / len(l)
    if max: res['max'] = l[-1]
    if min: res['min'] = l[0]
    if count: res['count'] = TiedValue(len(basic_list), [item.id for item in l])
    if median: res['median'] = l[len(l) // 2]
    if common:
        common_array = calculate_array_common(basic_list)
        res['commonMean'] = round(float(np.mean(common_array)), 1)
        res['commonMedian'] = round(float(np.median(common_array)), 1)

    if fourth:
        res['fourth'] = l[len(l) // 4]
        res['fourth2'] = l[len(l) // 4 * 3]

    return res


def list_get(tuple_list, key):
    return [
        item[1]
        for item in tuple_list
        if item[0] == key
    ]


def align_string(text, size):
    text = str(text)
    return text + ' ' * max(1, size - len(text) - 1)


def best_names_matches(items_dict, examples):
    def compare(a, b):
        seq = difflib.SequenceMatcher(a=a, b=b)
        return seq.ratio()

    def is_english(s):
        return re.sub(f'[{string.punctuation}a-zA-Z0-9 ]', '', s) == ''

    def is_russian(s):
        return re.sub(f'[{string.punctuation}а-яА-Я0-9 ]', '', s) == ''

    def clear(s):
        return re.sub(f'[{string.punctuation}]', '', s)

    def translit(s):
        try:
            return transliterate.translit(s, reversed=True)
        except:
            return None

    def prepare_string(s):
        s = clear(s.lower())
        if len(s) < 3:
            return None
        if is_english(s):
            return s
        elif is_russian(s):
            return translit(s)
        return None

    def item_evaluate_ratio(item, examples_list):
        return max([compare(item, example) for example in examples_list])

    items_dict_ = {}

    for key, value in items_dict.items():
        prepared_value = prepare_string(key)
        if prepared_value:
            items_dict_[prepared_value] = value

    good_examples = [prepare_string(s) for s in examples]
    good_examples = [i for i in good_examples if i]

    result = [
        (value, item_evaluate_ratio(key, good_examples))
        for key, value in items_dict_.items()
    ]
    result_dict = {}
    for key, value in result:
        result_dict[key] = max(result_dict.get(key, 0), value)

    return Counter(result_dict)


def value_to_color(x):
    x = 1 - x
    x = math.sqrt(x)
    x *= 255
    x = int(x)
    x += 50
    x = min(x, 255)
    x = max(0, x)
    color = hex(x)[2:].upper()
    if len(color) == 1:
        color += color
    return f'#{color * 3}'


def get_common_texts_terms(texts):
    assert isinstance(texts, list)

    def normalize_word(word):
        word = word.with_value(morph.parse(word.get_value())[0].normal_form)
        return word.sub('ия$|ический$', '')

    texts_words = []
    for text in texts:
        text = text.lower()
        text = text.sub(r'http\S+', ' ')
        text = text.sub('[^а-яa-z]', ' ')
        words = set([normalize_word(word) for word in text.split()])
        words -= most_frequent_words
        texts_words += list(words)

    return TiedCounter(texts_words)


class ThreadResult:
    def __init__(self, target=None, args=None, kwargs=None):
        self.result = None
        if not args:
            args = []
        if not kwargs:
            kwargs = {}

        def saver_func(*args_, **kwargs_):
            self.result = target(*args_, **kwargs_)

        self.thread = Thread(target=saver_func, args=args, kwargs=kwargs)
        self.thread.start()

    def execute(self):
        self.thread.join()
        return self.result


# Языковые функции

def round_num(value):
    if isinstance(value, str):
        return value
    return round(value, 2)


def to_string_time_period(timedelta):
    translate_dict = {
        's': {
            1: 'секунда',
            2: 'секунды',
            5: 'секунд',
        },
        'm': {
            1: 'минута',
            2: 'минуты',
            5: 'минут',
        },
        'h': {
            1: 'час',
            2: 'часа',
            5: 'часов',
        },
        'd': {
            1: 'день',
            2: 'дня',
            5: 'денй',
        },
        'y': {
            1: 'год',
            2: 'года',
            5: 'лет',
        },

    }

    seconds = (timedelta, 's')
    minutes = (seconds[0] / 60, 'm')
    hours = (minutes[0] / 60, 'h')
    days = (hours[0] / 24, 'd')
    years = (days[0] / 365, 'y')
    periods = [years, days, hours, minutes, seconds]

    for period in periods:
        r = round(period[0])
        if 0 < r and (abs(r - period[0]) < 0.2 or r > 1) or period[1] == 's':
            t = round(period[0]) % 10
            time_name = period[1]
            name = 'unknown'
            if t == 1:
                name = translate_dict[time_name][1]
            if t >= 2:
                name = translate_dict[time_name][2]
            if t >= 5 or t == 0:
                name = translate_dict[time_name][5]
            if r == 1:
                return name
            return f'{r} {name}'


def concatenate_lists(lists_array):
    res = []
    for item in lists_array:
        res = item + res
    return res


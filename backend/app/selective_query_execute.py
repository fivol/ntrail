import time
import re

from ntmodule.selective_query_exeptions import QueryLexicalException, QuerySyntaxException, QuerySemanticException, \
    WrongQueryException, QueryProgrammingException
from ntmodule.tools import timeit
from glbal import logger

from module_vk.module import ModuleVK
from module_query.module import ModuleQuery

modules_dict = {
    'vk': ModuleVK,
    'query': ModuleQuery
}

TOKEN_WORD = 'word'
TOKEN_TEXT = 'text'


class Token:
    def __init__(self, value):
        if value is None:
            self.token_type = None
            self.token_value = None
        elif not value:
            raise QuerySyntaxException('обнаружен пустой токен')
        elif value in '()[]=':
            self.token_type = value
            self.token_value = value
        elif value[0] == '"':
            self.token_type = TOKEN_TEXT
            self.token_value = value[1:-1]
        else:
            self.token_type = TOKEN_WORD
            self.token_value = value

    def __repr__(self):
        return f"Token('{self.value}')"

    @property
    def type(self):
        return self.token_type

    @property
    def value(self):
        return self.token_value

    def lower(self):
        return Token(self.value.lower())


class TokensGenerator:
    def __init__(self, tokens):
        self.tokens = tokens
        self.len = len(self.tokens)
        self.i = 0

    def peek(self):
        if not self.check():
            return Token(None)

        return self.tokens[self.i]

    def next(self, expected_type=None, to_lower_case=True):
        if not self.check():
            raise QueryLexicalException(f'неожиданный конец строки после "{self.tokens[-1]}"')

        token = self.peek()

        if expected_type and expected_type != token.type:
            raise QuerySyntaxException(f'встречен токен неверного типа "{token.type}" вместо "{expected_type}"')
        self.i += 1

        return token.lower()

    def check(self):
        return self.i < self.len


class QueryParser:
    def __init__(self, tokens_generator):
        self.g = tokens_generator

    def read_value(self):
        return self.g.next(to_lower_case=False).value

    def read_parameters(self):
        begin_sign = '['
        end_sign = ']'
        if self.g.peek().value != begin_sign:
            return {}
        self.g.next()
        parameters = {}
        while self.g.peek().value != end_sign:
            key = self.g.next(TOKEN_WORD).value
            value = True
            if self.g.peek().value == '=':
                self.g.next()
                value = self.read_value()
            parameters[key] = value

        self.g.next()

        return parameters

    def read_arguments(self):
        if self.g.peek().value == '(':
            arguments = []

            self.g.next()
            while self.g.peek().value != ')':
                arguments.append(self.read_value())

            self.g.next()
            return arguments
        else:
            return self.read_value()

    def read_attributes(self):
        attributes = []
        while self.g.peek().type == TOKEN_WORD:
            attribute = self.g.next().value
            attributes.append({
                'attribute': attribute,
                'parameters': self.read_parameters()
            })

        return attributes

    def read_method(self):
        separator = '.'
        method = self.g.next(TOKEN_WORD).value
        method_items = method.split(separator)
        if len(method_items) != 2:
            raise QuerySyntaxException(
                'название метода должно быть составлено по принципу <название модуля>.<имя метода>')
        module_name, method_name = method_items

        return module_name, method_name

    def read_action(self):
        method = self.read_method()
        parameters = self.read_parameters()
        arguments = self.read_arguments()
        attributes = self.read_attributes()
        return {
            'module': method[0],
            'action': method[1],
            'parameters': parameters,
            'arguments': arguments,
            'attributes': attributes
        }

    def read_query_method_name(self):
        method = self.g.next(TOKEN_WORD)
        return method.value

    def read_query_method(self):
        name = self.read_query_method_name()
        parameters = self.read_parameters()
        return {
            'name': name,
            'parameters': parameters
        }


def normalize(s):
    res = s.strip()
    if not res:
        return QuerySyntaxException('пустой запрос')
    return res


# @timeit
def get_query_tokens(query):
    groups = re.findall(r'"[^"]+"|[a-zA-Z0-9а-яА-Я._:/]+|[\[\]()=]', query)

    return [Token(value) for value in groups]


def get_module(module_name):
    if module_name not in modules_dict:
        raise QuerySemanticException(f'неизвестный модуль "{module_name}"')

    return modules_dict[module_name]


def execute_action(action):
    module_name = action['module']
    method_name = action['action']
    params = action['parameters']
    args = action['arguments']
    attrs = action['attributes']
    module = get_module(module_name)
    if not hasattr(module, method_name):
        raise QuerySemanticException(f'модуль "{module_name}" не содержит метод "{method_name}"')

    try:
        action_object = getattr(module, method_name)(args, **params)
        for attribute in attrs:
            attribute_name = attribute['attribute']
            parameters = attribute['parameters']
            if not hasattr(action_object, attribute_name) or attribute_name not in action_object.available_attributes:
                raise QuerySemanticException(f'метод "{method_name}" не поддерживает атрибут "{attribute_name}"')

            try:
                action_object = getattr(action_object, attribute_name)(**parameters)
            except TypeError:
                logger.exception('не корректные аргументы')
                raise QuerySemanticException(f'не корректные аргументы: "{parameters}" для метода "{attribute_name}"')

        return action_object

    except Exception as e:
        if not isinstance(e, WrongQueryException):
            logger.exception('Fail to initialize action %s in module %s', method_name, method_name)
        raise e


def call_method(class_object, method_name, params=None):
    if not params:
        params = {}
    if not hasattr(class_object, method_name):
        raise QueryProgrammingException(f'класс "{class_object.__class__.__name__}" не содержит метод "{method_name}"')
    return getattr(class_object, method_name)(**params)


def represent_object(obj, params=None):
    return call_method(obj, 'represent', params)


def query_get(params, parser):
    return represent_object(execute_action(parser.read_action()))


def query_load(params, parser):
    action = parser.read_action()
    action['parameters']['force'] = True
    return represent_object(execute_action(action), {'force': True})


def query_union():
    pass


@timeit
def collect_query_data(q):
    # Эта функция возвращает объект data, в котором должно лежать все необходимое, в качестве ответа на запрос и
    # ничего лишнего. Все побочные запросы идут через другой интерфейс
    q = normalize(q)
    g = TokensGenerator(get_query_tokens(q))
    parser = QueryParser(g)
    method = parser.read_query_method()
    method_name = method['name']
    method_parameters = method['parameters']

    if method_name == 'get':
        return query_get(method_parameters, parser)
    elif method_name == 'load':
        return query_load(method_parameters, parser)
    else:
        raise QuerySyntaxException(
            f'неизвесный тип запроса "{method_name}".\
             Возможные значения: GET, LOAD и другие (полное описание читайте в документации)'
        )


def execute_query(query):
    # Тут все начинается. Это функция wrapper над всем остальным. При необходимость нужно просто кидать ошибку
    # и не заморачиваться, как она политит дальше. Тут формируюся необходимые поля ответа
    response = {
        'code': 200,
        'error': '',
        'queryString': query,
    }
    execute_begin_time = time.time()
    data = {}
    try:
        data = collect_query_data(query)
    except WrongQueryException as e:
        response['error'] = e.get_text()
        response['code'] = e.code

    response['queryExecutionDuration'] = time.time() - execute_begin_time
    response['data'] = data

    return response

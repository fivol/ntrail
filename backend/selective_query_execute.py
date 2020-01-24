import time
import re
from vkuser import VKUser
from vkcommunity import VKCommunity


class WrongQueryException(Exception):
    def __init__(self, text, code=400):
        self.text = text
        self.code = code

    def get_text(self):
        return self.text


class QuerySyntaxException(WrongQueryException):
    def get_text(self):
        return f'Синтаксическая ошибка: {self.text}'


class QuerySemanticException(WrongQueryException):
    def get_text(self):
        return f'Семантическая ошибка: {self.text}'


class QueryLexicalException(WrongQueryException):
    def get_text(self):
        return f'Лексическая ошибка: {self.text}'


def base_syntax_check(s):
    pattern = r'[^a-zA-Zа-яА-Я"._0-9]'
    # result = re.search(pattern,  s)
    # if result:
    #     raise QuerySyntaxException(f'не ожидаемый символ {result.group(0)}')


def normalize(s):
    res = s.strip()
    if not res:
        return QuerySyntaxException('пустой запрос')
    return res


def get_query_tokens(query):
    groups = re.findall(r'"[^"]+"|[a-zA-Z0-9а-яА-Я._:/]+|[()]', query)

    tokens = []
    for group in groups:
        if group in '()':
            token_type = group
        elif group[0] == '"':
            token_type = 'text'
            group = group[1:-1]
        else:
            token_type = 'word'
        tokens.append((token_type, group))
    return tokens


class TokensGenerator:
    def __init__(self, tokens):
        self.tokens = tokens
        self.len = len(self.tokens)
        self.i = 0

    def peek(self):
        if not self.check():
            raise QueryLexicalException(f'неожиданный конец строки после "{self.tokens[-1]}"')
        return self.tokens[self.i]

    def next(self):
        token = self.peek()
        self.i += 1
        return token

    def check(self):
        return self.i < self.len


def state_machine(g, previous_object):
    def read_list(token_types=None):
        if not token_types:
            token_types = []
        if g.next()[0] != '(':
            raise QuerySyntaxException('ожидалась (')
        items = []
        while g.peek()[0] != ')':
            token_item = g.next()
            if token_item[0] not in token_types:
                raise QueryLexicalException(f'неверные тип токена списка: {token_item[1]}')
            items.append(token_item)
        g.next()
        return items

    def tokens_values(tokens):
        return [full_token[1] for full_token in tokens]

    token = g.next()
    (token_type, token_value) = token
    token_value = token_value.lower()
    if token_value == 'vkuser':
        user_id = g.next()
        if user_id[0] != 'word':
            raise QuerySemanticException(f'ожилался идентификатор пользователя, получен {user_id[1]}')
        return VKUser(user_id[1])
    if token_value == 'vkusers':
        users = read_list('word')
        if len(users) == 1:
            return VKUser(tokens_values(users)[0])
        return VKCommunity(tokens_values(users))
    if token_value == 'friends':
        if not hasattr(previous_object, 'friends'):
            raise QuerySemanticException('невозможно получить друзей данного объекта')
        return previous_object.friends()
    if token_type == '(':
        result = state_machine(g, previous_object)
        item = g.next()
        if item[0] != ')':
            raise QuerySyntaxException(f'ожидалась ")" вместо "{item[1]}"')
        return result

    raise QuerySyntaxException(f'встречен неизвестный токен "{token[1]}"')


def collect_query_data(q):
    # Эта функция возвращает объект data, в котором должно лежать все необходимое, в качестве ответа на запрос и
    # ничего лишнего. Все побочные запросы идут через другой интерфейс
    q = normalize(q)
    base_syntax_check(q)
    g = TokensGenerator(get_query_tokens(q))

    result = None
    while g.check():
        result = state_machine(g, result)

    if hasattr(result, 'represent'):
        return result.represent()
    return result


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

    response['data'] = data
    response['time'] = time.time()
    response['queryExecutionDuration'] = time.time() - execute_begin_time

    print(response)
    return response



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


class QueryProgrammingException(WrongQueryException):
    def get_text(self):
        return f'Ошибка программиста: {self.text}'


class QueryLexicalException(WrongQueryException):
    def get_text(self):
        return f'Лексическая ошибка: {self.text}'


class QueryDataException(WrongQueryException):
    def get_text(self):
        return f'Некорректные данные запроса: {self.text}'



class CredentialsServerApi:
    """Основной класс для получения данных авторизации
        Его задачи:
        1. Обращение к credentials-server за токенами и другими
        2. Хранение для быстрого доступа
        3. Возврат credentials-server с указанием причины
    """

    tokens = [
        '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'  # my app token
    ]

    @classmethod
    def get_keys(cls, count: int):
        # TODO Call Credentials server
        send_tokens = cls.tokens[:count]
        cls.tokens = cls.tokens[count:]
        return send_tokens

    @classmethod
    def return_keys(cls, tokens):
        # TODO Call Credentials server and return tokens
        cls.tokens += tokens

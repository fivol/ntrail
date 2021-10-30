import logging
import random

logger = logging.getLogger('credentials-api')


class CredentialsServerApi:
    """Основной класс для получения данных авторизации
        Его задачи:
        1. Обращение к credentials-server за токенами и другими
        2. Хранение для быстрого доступа
        3. Возврат credentials-server с указанием причины
    """

    tokens = [
        '14d0b68663a9922a0e5b6ed0660e6dd25fddbe3343f0b77b9c33024a1805ef6f9c3c280d91a3b1a97a929',  # some user (vk3)
        '607c9224cf10f1e605f7bd37c330371af668e8d22e5d7533a2e6f019919839e1ebf4feca77841bf18e11d',  # my token
        'ceb2be8419170500776cd691203ba6d3c6a64cc79dd428e870ca172431da2e22a8edaa87da851ae8fb64f',  # Terald
        '2dc1eecd699abfc38eaef9f978e4c3d398ace0acd0500e9489e8fbe1a06e106fee5d46991b0c89ca7876c',  # mdd
        '6564c4e0d209090cc04482143ffd2f4989538e805c8ba1cb154e34e2c724802af4233b32a04360fd8823f',  # Bot Leonardo
        '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1',  # my app token,
        '2c575b732c575b732c575b73b62c3822f022c572c575b7372603a3335071351c65615ca',  # ntrail-test
        'cf9bf7c1cf9bf7c1cf9bf7c119cfed5bb3ccf9bcf9bf7c1afa69923dbe3f15f2c1d48c3',  # NTrail
        '20a8f61c20a8f61c20a8f61cec20d07370220a820a8f61c404e2f9516047ffbb3627fb3',  # ntail-api
        '9600e9b69600e9b69600e9b6ca966ce146996009600e9b6cb44bd26027fa029ca5dca15',  # mdd
        'b0c92712b0c92712b0c927124fb0b0c5cdbb0c9b0c92712d1b56dc800555c5a85392e59',  # token1
        '7a36d58c7a36d58c7a36d58cd77a4f376f77a367a36d58c1b4a9e96de35d21a28e0efa6',  # token2
        '92e1bb2092e1bb2092e1bb20f1929859c5992e192e1bb20f39df0177f53304cdddedd8f',  # token3
        'ebfba2c0ebfba2c0ebfba2c0b4eb824026eebfbebfba2c08a87e995bfc8dd6139c04236',  # token4
    ]

    @classmethod
    def get_keys(cls, count: int):
        return random.choices(cls.tokens, k=count)
        logger.debug('Get keys: %s', count)
        # TODO Call Credentials server
        send_tokens = cls.tokens[:count]
        cls.tokens = cls.tokens[count:]
        return send_tokens

    @classmethod
    def return_keys(cls, tokens):
        # TODO Call Credentials server and return tokens
        cls.tokens += tokens

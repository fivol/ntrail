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

    keys = {
        'vk.app.token': [
            '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1',  # my app token,
            '2c575b732c575b732c575b73b62c3822f022c572c575b7372603a3335071351c65615ca',  # ntrail-test
            'cf9bf7c1cf9bf7c1cf9bf7c119cfed5bb3ccf9bcf9bf7c1afa69923dbe3f15f2c1d48c3',  # NTrail
            '20a8f61c20a8f61c20a8f61cec20d07370220a820a8f61c404e2f9516047ffbb3627fb3',  # ntail-api
            '9600e9b69600e9b69600e9b6ca966ce146996009600e9b6cb44bd26027fa029ca5dca15',  # mdd
            'b0c92712b0c92712b0c927124fb0b0c5cdbb0c9b0c92712d1b56dc800555c5a85392e59',  # token1
            '7a36d58c7a36d58c7a36d58cd77a4f376f77a367a36d58c1b4a9e96de35d21a28e0efa6',  # token2
            '92e1bb2092e1bb2092e1bb20f1929859c5992e192e1bb20f39df0177f53304cdddedd8f',  # token3
            'ebfba2c0ebfba2c0ebfba2c0b4eb824026eebfbebfba2c08a87e995bfc8dd6139c04236',  # token4
            'd42df59ad42df59ad42df59adfd45416ffdd42dd42df59ab55164fc90f07dad999d9e66',  # token5
            '394f41a1394f41a1394f41a1fd3936a2c73394f394f41a15833d0de69d195716057f7f2',  # token6
            'a5d16764a5d16764a5d1676454a5a88403aa5d1a5d16764c4adf6fd8c23ac5104837e8a',  # token7
            '5fbcca0e5fbcca0e5fbcca0e105fc5296655fbc5fbcca0e3ec05bbfac31d550761a7846',  # token8
            'c902ef28c902ef28c902ef2854c97b0c41cc902c902ef28a87e7ee54f81aa27aa0eed16',  # token9
            'c7143605c7143605c7143605a8c76dd56fcc714c7143605a668a7e17f7e838c2bad8238',  # token10
        ],
        'vk.user.token': [
            '14d0b68663a9922a0e5b6ed0660e6dd25fddbe3343f0b77b9c33024a1805ef6f9c3c280d91a3b1a97a929',  # some user (vk3)
            '607c9224cf10f1e605f7bd37c330371af668e8d22e5d7533a2e6f019919839e1ebf4feca77841bf18e11d',  # my token
            'ceb2be8419170500776cd691203ba6d3c6a64cc79dd428e870ca172431da2e22a8edaa87da851ae8fb64f',  # Terald
            '2dc1eecd699abfc38eaef9f978e4c3d398ace0acd0500e9489e8fbe1a06e106fee5d46991b0c89ca7876c',  # mdd
            '6564c4e0d209090cc04482143ffd2f4989538e805c8ba1cb154e34e2c724802af4233b32a04360fd8823f',  # Bot Leonardo
        ]
    }

    @classmethod
    def get_keys(cls, key_type, count):
        keys = cls.keys[key_type]
        # TODO Call Credentials server
        send_keys = keys[:count]
        cls.keys[key_type] = keys[count:]
        return send_keys

    @classmethod
    def return_keys(cls, key_type, keys):
        # TODO Call Credentials server and return tokens
        cls.keys[key_type] += keys

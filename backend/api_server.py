from vkapi_remote import VKAPI
from igapi_remote import IGAPI
from constants import ACCOUNT_STATUS_BANNED

api_dict = {'vk': VKAPI, 'ig': IGAPI}


# Заменяет сервер, обрабатывающий и распределяющий входящие апи запросы
# Нужен для теста в пределах одного скрипта
class APIServerEmulator:

    @classmethod
    def incoming_request(cls, request_json):
        print(request_json)
        # Это просто для проверки работоспособности системы. Тут должно быть релизовано декадирование запросов
        # группировка по сервису, группировка по объему типу и отправка нужному серверу (в данном случае классу)
        assert isinstance(request_json, list)
        results = []
        for request in request_json:
            service = request['service']
            api_class = api_dict[service]
            method = request['method']
            params = request['params']
            if params is None:
                params = {}
            if hasattr(api_class, method):
                ans = getattr(api_class, method)(request['key'], **params)
                results.append(ans)

        return results

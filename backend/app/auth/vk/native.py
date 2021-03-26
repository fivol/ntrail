from auth.vk.datatypes import VKAccessToken
from config import HOST, VK_APP_SECRET, VK_APP_ID
import requests
from exceptions import HandledException

from glbal import logger

redirect_uri = f'{HOST}/auth/vk/'


class VKNativeAuthFlow:
    """Класс содержит методы, непосредственно оперирующие с сайтом вк
    и проводящие все этапы авторизации. Используется классом
    VKAuthorization - соединяющим этим методы, логику сервиса и работу с базами данных
    В соответствии с Authorization Code Flow https://vk.com/dev/authcode_flow_user
    """

    @staticmethod
    def get_access_token(code: str) -> VKAccessToken:
        assert code
        print(code)
        url = 'https://oauth.vk.com/access_token'
        response = requests.get(url, params={
            'code': code,
            'redirect_uri': redirect_uri,
            'client_secret': VK_APP_SECRET,
            'client_id': VK_APP_ID
        })
        if response.status_code != 200:
            logger.error('Fail to get vk access token %s', response.json())
            raise HandledException
        response.raise_for_status()
        json_body = response.json()
        if 'access_token' not in json_body:
            logger.error('Ошибка получения access_token')
            raise HandledException

        return VKAccessToken.parse_obj(json_body)

import datetime
import math
from contextlib import suppress
from enum import Enum, auto
from typing import Optional

import aiohttp
from fastapi import FastAPI, Query, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from models import Token, db, db_url
from config import config
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
from core.modules.vk.vkuser import VKUser

from tools import SmartAccessDict

app = FastAPI(
    title='NTrail API',
    version=config.get('VERSION'),
    description='[Читать описание API на Gitbook](https://borisoffficial.gitbook.io/ntrail-api/). '
                'Там подробно про каждый метод, лимиты, получение токена и т.д.'
)


@app.on_event("startup")
async def startup_event():
    await db.set_bind(db_url)


@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def index():
    return RedirectResponse("/version/")


@app.get('/version/', response_model=str)
async def version():
    """Текущая версия API"""
    return config.get('VERSION')


class VkRequestOption(Enum):
    # Только базовая информация о пользователе
    basic = 'basic'
    # Анализировать связи с друзьями, подписчиками и прочее
    connections = 'connections'


class ResponseVerbose(Enum):
    """Уровень детализации информации в запросе"""
    # Параметр по умолчанию, возвращать среднее количество информации
    normal = 'normal'
    # Упрощенный запрос, только необходимый минимум
    simple = 'simple'
    # Подробная инфа по запросу
    detail = 'detail'


class VkUserResponse(BaseModel):
    user: Optional[dict]


async def get_token(vk_id: str):
    """Получаем токен"""
    token = await Token.query.where(Token.id == vk_id).gino.first()
    if not token:
        token = await Token.create(auth_method='vk', id=vk_id)
    return token.token


async def check_token(token: str, **kwargs):
    """Проверяет токен на валидность. И возвращает связанные с ним данные"""
    model = await Token.query.where(Token.token == token).gino.first()
    if not model:
        raise HTTPException(status_code=401, detail="You should provide correct access token")


@app.get('/verify/', response_class=PlainTextResponse, include_in_schema=False)
async def vk_token_confirm(code: str):
    """Получаем vk_id человека и выдаем ему токен"""
    vk_access_token_url = 'https://oauth.vk.com/access_token'
    async with aiohttp.ClientSession() as session:
        async with session.get(vk_access_token_url, params={
            'client_id': config.get('VK_APP.CLIENT_ID'),
            'client_secret': config.get('VK_APP.SECRET'),
            'code': code,
            'redirect_uri': f'{config.get("BASE_URL")}/verify/'
        }) as response:
            try:
                response = await response.json()
                vk_id = response['user_id']
            except:
                return "Reloading page prohibited. Please, pass original link"
    return bytes(await get_token(vk_id), 'utf-8')


class PropertySource(Enum):
    page = auto()
    friends = auto()
    followers = auto()
    following = auto()


@app.get('/vk/', response_model=VkUserResponse, name='ВК аккаунт')
async def vk_api(token: str = Query(None, title='API токен'),
                 options: list[VkRequestOption] = Query(['basic'], title='API токен'),
                 verbose: ResponseVerbose = Query(ResponseVerbose.normal, title='Детализация ответа'),
                 user: str = Query(..., title='Аккаунт ВК',
                                   description='username, ссылка или id пользователя ВК', min_length=2
                                   )) -> dict:
    """Получить информацию об одном аккаунте ВКонтакте. Запрос собирается на основе списка `options` из аргументов
    Возможны следующие варианты
    - basic: только данные самого аккаунта, самые быстрый запрос, возвращает следующую информацию
    """
    await check_token(token)

    if not options:
        options.append(VkRequestOption.basic)
    options = set(options)

    # Данные, которые возвращает запрос
    user_data = {}
    user = VKUser(user)
    if not user.valid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    def add_property(key: str, value, confidence: float = None, source: PropertySource = None):
        """Добавить значение к ответу"""
        if value is None:
            return
        if verbose == ResponseVerbose.simple:
            user_data[key] = value
        elif verbose == ResponseVerbose.normal:
            property_dict = {
                'value': value
            }
            if source:
                property_dict['source'] = source.name
            if confidence is not None:
                property_dict['confidence'] = min(1.0, max(0.0, confidence))
            user_data[key] = property_dict
        else:
            raise ValueError

    if VkRequestOption.basic in options:
        add_property('id', user.id, source=PropertySource.page)
        add_property('url', user.url, source=PropertySource.page)
        add_property('name', user.name, source=PropertySource.page)
        add_property('username', user.get_attribute('screen_name'), source=PropertySource.page)
        add_property('deactivated', user.get_attribute('deactivated'), source=PropertySource.page)
        add_property('sex', ['not specified', 'female', 'male'][user.get_attribute('sex', 0)],
                     source=PropertySource.page)
        bdate = user.get_attribute('bdate')
        add_property('birth', bdate, source=PropertySource.page)
        add_property('photo', user.get_attribute('photo_200'), source=PropertySource.page)
        # Возраст, взятый напрямую со страницы
        if bdate and len(bdate.split('.')) == 3:
            age = datetime.datetime.now() - datetime.datetime.strptime(bdate, '%d.%m.%Y')
            add_property('age', age.days // 365)

    if VkRequestOption.connections in options:
        from core.modules.vk.vkcommunity import VKCommunity
        friends: VKCommunity = user.friends()
        friends_data = friends.process_data()

        def extract_first(key):
            return {
                'key': key,
                'value': friends_data[key]['source_list'][0][0].value,
                'confidence': round(len(friends_data[key]['source_list'][0][0].id) / len(friends), 2)
            }

        add_property('friends_count', len(friends), source=PropertySource.friends)
        with suppress(Exception):
            if friends_data['age']['count'] > 4:
                add_property('age', friends_data['age']['commonMedian'], source=PropertySource.friends,
                             confidence=len(friends) / 100)
        with suppress(Exception):
            add_property(**extract_first('city'))
        with suppress(Exception):
            add_property(**extract_first('country'))
        with suppress(Exception):
            add_property(**extract_first('school'))
        with suppress(Exception):
            add_property(**extract_first('university'))
        clusters = friends.pools()
        add_property('social.groups.all.count', len([cluster for cluster in clusters if len(cluster) > 3]))
        add_property('social.groups.big.count', len([cluster for cluster in clusters if len(cluster) > 8]))
        add_property('social.groups.small.count',  len([cluster for cluster in clusters if 1 < len(cluster) <= 8]))
        add_property('social.groups.free.count',  len([cluster for cluster in clusters if len(cluster) == 1]))

    return {
        'user': user_data
    }

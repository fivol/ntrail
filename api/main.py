import datetime
import math
from contextlib import suppress
from enum import Enum, auto
from typing import Optional

import aiohttp
from fastapi import FastAPI, Query, HTTPException, status
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
    # Группы и сообщества человека
    groups = 'groups'


class ResponseVerbose(Enum):
    """Уровень детализации информации в запросе"""
    # Параметр по умолчанию, возвращать среднее количество информации
    normal = 'normal'
    # Упрощенный запрос, только необходимый минимум
    simple = 'simple'
    # Подробная инфа по запросу
    # detail = 'detail'


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
        if value is None or value == '':
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
        with suppress(Exception):
            platform = user.get_attribute('last_seen')['platform']
            add_property('platform.type', [None, 'web', 'apple', 'apple', 'android', 'web', 'web', 'web'][platform],
                         source=PropertySource.page)
        add_property('followers.count', user.get_attribute('followers_count'), source=PropertySource.page)
        with suppress(Exception):
            add_property('subscriptions.count', user.get_attribute('counters')['subscriptions'],
                         source=PropertySource.page)
            add_property('followers.count', user.get_attribute('counters')['followers'], source=PropertySource.page)
        with suppress(Exception):
            add_property('occupation', user.get_attribute('occupation')['type'], source=PropertySource.page)
        with suppress(Exception):
            add_property('university', user.get_attribute('universities')[0]['name'], source=PropertySource.page)
        with suppress(Exception):
            add_property('school', user.get_attribute('schools')[0]['name'], source=PropertySource.page)

        with suppress(Exception):
            add_property('active_user',
                         datetime.datetime.now() - datetime.datetime.fromtimestamp(
                             user.get_attribute('last_seen')['time']) < datetime.timedelta(days=3),
                         source=PropertySource.page)
        add_property('relation',
                     [None, 'single', 'in a relationship', 'engaged', 'married', "it's complicated",
                      'actively searching', 'in love'][user.get_attribute('relation')])
        with suppress(Exception):
            add_property('personal',
                         [None, 'Communist', 'Socialist', 'Moderate', 'Liberal', "Conservative",
                          'Monarchist', 'Ultraconservative', 'Apathetic', 'Libertian'][
                             user.get_attribute('personal')['political']])
        if user.get_attribute("instagram"):
            add_property('links.instagram', f'https://www.instagram.com/{user.get_attribute("instagram")}/')

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

        add_property('friends.count', len(friends), source=PropertySource.friends)
        with suppress(Exception):
            if friends_data['age']['count'].value > 4:
                add_property('age', friends_data['age']['commonMedian'], source=PropertySource.friends,
                             confidence=friends_data['age']['count'].value / 100)
        with suppress(Exception):
            add_property(**extract_first('city'))
        with suppress(Exception):
            add_property(**extract_first('country'))
        with suppress(Exception):
            if not len(user.get_attribute('schools', [])):
                add_property(**extract_first('school'))
        with suppress(Exception):
            if not len(user.get_attribute('universities', [])):
                add_property(**extract_first('university'))
        clusters = friends.pools()
        add_property('social.groups.all.count', len([cluster for cluster in clusters if len(cluster) > 3]))
        add_property('social.groups.big.count', len([cluster for cluster in clusters if len(cluster) > 8]))
        add_property('social.groups.small.count', len([cluster for cluster in clusters if 1 < len(cluster) <= 8]))
        add_property('social.groups.free.count', len([cluster for cluster in clusters if len(cluster) == 1]))

    if VkRequestOption.groups in options:
        groups = user.groups()
        add_property('groups.count', len(groups))
        groups_data = groups.process_data()
        add_property('groups.themes', [item[0].value for item in groups_data['activity_pages']['source_list']])
        add_property('groups.tags', [item[0].value for item in groups_data['name']['source_list']])

    return {
        'user': user_data
    }

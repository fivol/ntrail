from enum import Enum
from typing import Optional

import aiohttp
from fastapi import FastAPI, Query, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from models import Token, db, db_url
from config import config
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
from core.modules.vk.vkuser import VKUser

from utils import SmartAccessDict

app = FastAPI(
    title='NTrail API',
    version=config.get('VERSION')
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


class VkRequestOption(str, Enum):
    # Только базовая информация о пользователе
    basic = 'basic'
    # Помимо аккаунта цели, получить список друзей
    friends = 'friends'
    # Сгруппировать друзей по кластерам и проанализировать их
    clusters = 'clusters'


class ResponseVerbose(str, Enum):
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


@app.get('/vk/', response_model=VkUserResponse, name='ВК аккаунт')
async def vk_api(response: Response,
                 token: str = Query(None, title='API токен'),
                 options: list[VkRequestOption] = Query(..., title='API токен'),
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

    if VkRequestOption.basic in options:
        user = VKUser(user)
        if not user.valid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
        user_data['id'] = user.id
        user_data['username'] = user.get_attribute('')
        user_data['name'] = user.name
        user_data['url'] = user.url

    return {
        'user': user_data
    }

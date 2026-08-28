from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import aiohttp

from server.models import Token
from server.config import config

router = APIRouter()


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


@router.get('/verify/', response_class=PlainTextResponse, include_in_schema=False)
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
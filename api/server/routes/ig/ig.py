import logging
from fastapi import APIRouter, Query, HTTPException, status, Depends
from server.routes.request import execute_api_request, common_parameters

from worker import VKError

router = APIRouter(prefix='/ig')

logger = logging.getLogger(__name__)


@router.get('/user/')
async def ig_user(commons: dict = Depends(common_parameters),
                  user: str = Query(..., title='Аккаунт Instagram',
                                    description='Username, ссылка или id пользователя Instagram',
                                    min_length=2)) -> dict:
    """
    - basic: только базовая информация о пользователе
    - connections: анализировать связи с друзьями, подписчиками и прочее
    - groups: группы и сообщества человека
    """
    # TODO Do not initialize all sessions for each request
    kwargs = {'user': user}
    return await execute_api_request(kwargs=kwargs, input_plugins=['user'], options=commons['options'])

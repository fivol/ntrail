import asyncio
import logging

from fastapi import APIRouter, Query

from server.plugin.plugin_manager import PluginManager
from server.types import ResponseVerbose

from worker import Engine

router = APIRouter(prefix='/vk')

logger = logging.getLogger('vk-route')


@router.get('/')
def vk_analysis(token: str = Query(None, title='API токен'),
                options: list[str] = Query(['user'], title='Опиции запроса, список необходимых плагинов'),
                verbose: ResponseVerbose = Query(ResponseVerbose.simple, title='Детализация ответа'),
                user: str = Query(..., title='Аккаунт ВК',
                                  description='Username, ссылка или id пользователя ВК', min_length=2)) -> dict:
    """

    - basic: только базовая информация о пользователе
    - connections: анализировать связи с друзьями, подписчиками и прочее
    - groups: группы и сообщества человека
    """
    asyncio.set_event_loop(asyncio.new_event_loop())
    kwargs = {'user': user}
    with Engine(caching=False):
        manager = PluginManager(kwargs=kwargs, input_plugins=['user'], options=options)
        return manager.execute()

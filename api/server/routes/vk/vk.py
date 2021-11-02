import asyncio
import logging

from fastapi import APIRouter, Query

from server.plugin_manager import PluginManager
from server.types import ResponseVerbose

from server.routes.vk.plugins.basic import VKBasicPlugin
from server.routes.vk.plugins.friends import VKFriendsPlugin
from server.routes.vk.plugins.user import VKUserPlugin, VKUserDataPlugin
from server.routes.vk.plugins.groups import VKGroupsPlugin
from worker import Engine

router = APIRouter(prefix='/vk')

logger = logging.getLogger('vk-route')

plugins = [VKGroupsPlugin, VKUserPlugin, VKFriendsPlugin, VKBasicPlugin, VKUserDataPlugin]


@router.get('/')
def vk_analysis(token: str = Query(None, title='API токен'),
                options: list[str] = Query(['basic'], title='Опиции запроса, список необходимых плагинов'),
                verbose: ResponseVerbose = Query(ResponseVerbose.simple, title='Детализация ответа'),
                user: str = Query(..., title='Аккаунт ВК',
                                  description='Username, ссылка или id пользователя ВК', min_length=2)) -> dict:
    """

    - basic: только базовая информация о пользователе
    - connections: анализировать связи с друзьями, подписчиками и прочее
    - groups: группы и сообщества человека
    """
    asyncio.set_event_loop(asyncio.new_event_loop())
    args = {'user': user}
    with Engine():
        manager = PluginManager(plugins, args, verbose=verbose, options=options)
        return manager.execute()

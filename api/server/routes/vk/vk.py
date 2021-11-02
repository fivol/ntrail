from fastapi import APIRouter, Query

from server.plugin_manager import PluginManager
from server.routes.vk.plugins.friends import VKFriendsPlugin
from server.types import ResponseVerbose

router = APIRouter(prefix='/vk')


@router.get('/')
def vk_user(token: str = Query(None, title='API токен'),
            options: list[str] = Query(['basic'], title='Опиции запроса, список необходимых плагинов'),
            verbose: ResponseVerbose = Query(ResponseVerbose.simple, title='Детализация ответа'),
            user: str = Query(..., title='Аккаунт ВК',
                              description='username, ссылка или id пользователя ВК', min_length=2
                              )) -> dict:
    """

    - basic: только базовая информация о пользователе
    - connections: анализировать связи с друзьями, подписчиками и прочее
    - groups: группы и сообщества человека
    """
    args = {'user': user}
    manager = PluginManager([VKFriendsPlugin], args, verbose=verbose, options=options)
    return manager.execute()

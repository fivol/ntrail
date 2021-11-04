import asyncio
import logging

from fastapi import APIRouter, Query, HTTPException, status

from server.exceptions import ServerError, WrongInputError
from server.plugin.plugin_manager import PluginManager
from server.types import ResponseVerbose
from server.config import config

from worker import Engine, VKError

router = APIRouter(prefix='/vk')

logger = logging.getLogger('vk-route')


@router.get('/user/')
def vk_user(token: str = Query(None, title='API токен'),
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
    with Engine(caching=config.bool('CACHING')):
        manager = PluginManager(kwargs=kwargs, input_plugins=['user'], options=options)
        try:
            result = manager.execute()
            logger.debug('Response: %s', result)
            return result
        except VKError as e:
            raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY,
                                detail={'code': e.code, 'type': e.type.name, 'message': e.msg})
        except ServerError as e:
            logger.exception('ServerError')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        except WrongInputError as e:
            logger.exception('WrongInputError')
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception:
            logger.exception('Unknown server exception')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

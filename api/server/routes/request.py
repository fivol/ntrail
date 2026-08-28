from loguru import logger

from fastapi import HTTPException, status, Query

from server.exceptions import NtrailServerError, NtrailWrongInputError
from server.plugin.plugin_manager import PluginManager
from server.types import ResponseVerbose


async def common_parameters(token: str = Query(None, title='API токен'),
                            verbose: ResponseVerbose = Query(ResponseVerbose.simple, title='Детализация ответа'),
                            options: list[str] = Query(['user'],
                                                       title='Опиции запроса, список необходимых плагинов'), ):
    return {
        'options': options,
        'verbose': verbose
    }


async def execute_api_request(kwargs, input_plugins, options, namespace=None):
    try:
        manager = PluginManager(kwargs=kwargs, input_plugins=input_plugins, options=options, namespace=namespace)
        result = await manager.execute()
        logger.debug('Response: {}', result)
        return result
    except NtrailServerError as e:
        logger.exception('ServerError')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except NtrailWrongInputError as e:
        logger.info('WrongInputError')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception('Unknown server exception')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

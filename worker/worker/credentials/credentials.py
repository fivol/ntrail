import asyncio
from loguru import logger

from worker.credentials.access import AccessModel
from worker.credentials.adapter import AdapterBase
from worker.credentials.adapters.ig import IGAdapter
from worker.credentials.adapters.vk import VKAdapter
from worker.credentials.db import AccessStatus, AccountsAccess
from worker.credentials.models import DBAccess


adapters = {
    'vk': VKAdapter,
    'ig': IGAdapter
}


class Credentials:
    """Основной класс для получения данных авторизации
        Его задачи:
        1. Обращение к credentials-server за токенами и другими
        2. Хранение для быстрого доступа
        3. Возврат credentials-server с указанием причины
    """

    @classmethod
    def _get_adapter(cls, name: str) -> type(AdapterBase):
        return adapters[name]

    @classmethod
    def _create_model(cls, model: DBAccess):
        return AccessModel(model)

    @classmethod
    async def get_access(cls, key_type: str, count: int = None, ids=None) -> list[AccessModel]:
        if '.' in key_type:
            service, type_ = key_type.split('.', 1)
        else:
            service, type_ = key_type, None
        models = await cls._get_adapter(service).get_access(type_=type_, max_count=count, ids=ids)
        logger.info('Acquire {} keys', len(models))
        return list(map(cls._create_model, models))

    @classmethod
    async def update_access(cls, models: list[DBAccess]):
        logger.info('Update access ({})', len(models))
        await AccountsAccess.update_access(models)

    @classmethod
    async def return_access(cls, models: list[AccessModel], error: AccessStatus = None):
        models = list(map(lambda model: model.row(), models))
        if not models:
            return
        if error:
            logger.error('Return access with error: {}', error)
            for key in models:
                await AccountsAccess.set_access_status(key, error)
            return
        await AccountsAccess.return_access(models)

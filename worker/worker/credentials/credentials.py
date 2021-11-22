import logging

from worker.credentials.adapter import AdapterBase
from worker.credentials.adapters.ig import IGAdapter
from worker.credentials.adapters.vk import VKAdapter
from worker.credentials.db import AccessStatus, AccountsAccess
from worker.credentials.models import DBAccess

logger = logging.getLogger(__name__)

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
    async def get_access(cls, key_type: str, count: int = None) -> list[dict]:
        service, type_ = key_type.split('.', 1)
        models = await cls._get_adapter(service).get_access(type_=type_, max_count=count)
        logger.info('Acquire %s keys', len(models))
        return models

    @classmethod
    async def update_access(cls, models: list[DBAccess]):
        logger.info('Update access (%s)', len(models))
        await AccountsAccess.update_access(models)

    @classmethod
    async def return_access(cls, models: list[DBAccess], error: AccessStatus = None):
        if not models:
            return
        if error:
            logger.error('Return access with error: %s', error)
            for key in models:
                await AccountsAccess.set_access_status(key, error)
            return
        await AccountsAccess.return_access(models)

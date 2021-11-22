import logging

from worker.credentials.adapter import AdapterBase
from worker.credentials.adapters.ig import IGAdapter
from worker.credentials.adapters.vk import VKAdapter
from worker.credentials.db import AccessStatus, AccountsAccess

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
    async def get_accesses(cls, service: str, key_type: str, count: int = None):

        return await cls._get_adapter(service).get_access(type_=key_type, max_count=count)

    @classmethod
    async def return_accesses(cls, accesses, error: AccessStatus = None):
        if error:
            logger.error('Return access with error: %s', error)
            for key in accesses:
                await AccountsAccess.set_access_status(key, error)
            return
        # TODO

import logging

from worker.credentials.adapter import AdapterBase
from worker.credentials.models import DBAccount

from asyncpg.exceptions import UniqueViolationError

logger = logging.getLogger(__name__)


class VKAdapter(AdapterBase):
    pass

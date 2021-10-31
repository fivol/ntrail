import warnings

from core.constants import CacheType

PLOT_CIRCULAR = 'circular'

warnings.simplefilter("ignore")


# Способ кеширования
# CACHE_TYPE_FULL_USE - максимальное возможное
# TODO Add other ways to cache requests description
CACHE_TYPE = CacheType.FULL_USE

API_SERVER_REQUEST_VERSION = 0

import logging.config
from bestconfig import Config

logger = logging.getLogger(__name__)
logging_config = Config('logging.yml', exclude_default=True)
logging.config.dictConfig(logging_config.to_dict())


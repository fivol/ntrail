import os
import warnings
import logging.config
from bestconfig import Config

from core.constants import CacheType

PLOT_CIRCULAR = 'circular'
warnings.simplefilter("ignore")
config = Config()


# Способ кеширования
# CACHE_TYPE_FULL_USE - максимальное возможное
# TODO Add other ways to cache requests description
CACHE_TYPE = CacheType.FULL_USE

if not os.environ.get('LOGGING_CONFIGURED'):
    logging.config.dictConfig(config.logging.to_dict())
    logger = logging.getLogger(__name__)


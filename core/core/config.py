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

logger = logging.getLogger(__name__)
logging.config.dictConfig(config.logging.to_dict())

import warnings
import logging.config
from bestconfig import Config


warnings.simplefilter("ignore")
config = Config()

logging.config.dictConfig(config.logging.to_dict())
logger = logging.getLogger(__name__)


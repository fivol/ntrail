import warnings
import logging.config
from bestconfig import Config


warnings.simplefilter("ignore")
config = Config()

log_config = config.logging.to_dict()
if not config.bool('DEBUG'):
    log_config['root']['level'] = 'WARNING'

logging.config.dictConfig(log_config)
logging.getLogger(__name__)

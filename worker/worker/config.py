import logging.config
from bestconfig import Config
import os


config = Config()
assert config.contains('DEBUG'), 'Probably you miss specify config.yml file with necessary variables'

if not os.environ.get('LOGGING_CONFIGURED'):
    logging.config.dictConfig(config.logging.to_dict())
    logger = logging.getLogger(__name__)

os.environ['LOGGING_CONFIGURED'] = 'true'

if not config.bool('DEBUG'):
    logging.disable(logging.WARNING)

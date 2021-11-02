import logging.config
from bestconfig import Config


config = Config()
assert config.contains('DEBUG'), 'Probably you miss specify config.yml file with necessary variables'

logger = logging.getLogger(__name__)
logging.config.dictConfig(config.logging.to_dict())

if not config.bool('DEBUG'):
    logging.disable(logging.WARNING)

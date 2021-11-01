import logging.config
from bestconfig import Config

logger = logging.getLogger(__name__)
logging_config = Config('logging.yml', exclude_default=True)
logging.config.dictConfig(logging_config.to_dict())


config = Config()
assert config.contains('DEBUG'), 'Probably you miss specify config.yml file with necessary variables'

if not config.bool('DEBUG'):
    logging.disable(logging.WARNING)

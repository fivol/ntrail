import logging.config
from bestconfig import Config

config = Config(exclude=['env_file'])
assert config.contains('DEBUG'), 'Probably you miss specify config.yml file with necessary variables'

log_config = config.logging.to_dict()
if not config.bool('DEBUG'):
    log_config['root']['level'] = 'WARNING'

logging.config.dictConfig(log_config)
logging.getLogger(__name__)


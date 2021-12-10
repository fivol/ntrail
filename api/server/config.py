import os

from bestconfig import Config
from logging.config import dictConfig

config = Config(exclude=['env_file'])
config.assert_contains('DEBUG')

log_config = config.logging.to_dict()
if not config.bool('DEBUG'):
    log_config['root']['level'] = 'WARNING'

dictConfig(log_config)

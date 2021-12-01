import os

from bestconfig import Config
import logging

config = Config(exclude=['env_file'])
config.assert_contains('DEBUG')

log_config = config.logging.to_dict()
if not config.bool('DEBUG'):
    log_config['root']['level'] = 'WARNING'

logging.config.dictConfig(log_config)

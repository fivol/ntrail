import os

from bestconfig import Config
import logging

config = Config(exclude=['env_file'])
config.assert_contains('DEBUG')

logging.config.dictConfig(config.logging.to_dict())
os.environ['LOGGING_CONFIGURED'] = 'true'

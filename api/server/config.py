import sys

from bestconfig import Config
from loguru import logger
logger.remove()
logger.add(sys.stdout, serialize=True)

config = Config('local-config.yml', exclude=['env_file'])

config.assert_contains('DEBUG')

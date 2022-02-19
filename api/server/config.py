import sys

import json_logging
from bestconfig import Config
from loguru import logger

config = Config(exclude=['env_file'])
config.assert_contains('DEBUG')


logger.remove()
logger.add(sys.stdout, serialize=False)

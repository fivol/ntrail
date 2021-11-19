import logging.config
from bestconfig import Config

config = Config()
assert config.contains('DEBUG'), 'Probably you miss specify config.yml file with necessary variables'

logging.config.dictConfig(config.logging.to_dict())


from bestconfig import Config
import logging

config = Config()

logging.config.dictConfig(config.logging.to_dict())


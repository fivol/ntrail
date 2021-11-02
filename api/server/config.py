from bestconfig import Config
import logging

config = Config()
config.assert_contains('DEBUG')

logging.config.dictConfig(config.logging.to_dict())
config.logging_configured = True


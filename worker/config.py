import logging.config
from bestconfig import Config

logger = logging.getLogger(__name__)
logging_config = Config('logging.yaml', exclude_default=True)
logging.config.dictConfig(logging_config.to_dict())

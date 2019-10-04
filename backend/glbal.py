import logging

logger = logging.getLogger('base_logger')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()

formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.debug('Start logging...')

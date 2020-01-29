import logging

import logging
logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


logger = logging.getLogger('base_logger')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()

formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

if __name__ == '__main__':
    logger.debug('Start logging...')

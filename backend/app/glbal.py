import logging

from visual_logging import VisualLogger

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)


logger = logging.getLogger('base_logger')
logger.setLevel(logging.WARNING)

handler = logging.StreamHandler()

formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

stack_logger = VisualLogger(online=True, min_duration_time=0.01, file='stack_logger.log')

if __name__ == '__main__':
    logger.debug('Start logging...')

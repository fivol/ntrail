from constants import CACHE_TYPE_FULL_USE
import os
from glbal import logger

DB_USER = 'postgres'
DB_HOST = 'localhost'
DB_PASS = 'postgres'
DB_NAME = 'ntrail'
DB_PORT = '5432'

try:
    if os.environ.get('ENV') == 'DOCKER':
        logger.info('DOCKER environment')
        DB_PASS = os.environ['POSTGRES_PASSWORD']
        DB_USER = os.environ['POSTGRES_USER']
        DB_NAME = os.environ['POSTGRES_DB']
        DB_HOST = 'db'

    else:
        logger.info('LOCALHOST environment')

except:
    logger.exception('Fail to get environment variables for db connection')

VERSION = '2.11.2'
API_SERVER_REQUEST_VERSION = 0

# Способ кеширования
# CACHE_TYPE_FULL_USE - максимальное возможное
# TODO Add other ways to cache requests description
CACHE_TYPE = CACHE_TYPE_FULL_USE

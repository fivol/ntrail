from constants import CACHE_TYPE_FULL_USE, CACHE_TYPE_IGNORE, CACHE_TYPE_ONLY_READ, CACHE_TYPE_ONLY_WRITE
import os
from glbal import logger

DB_USER = 'postgres'
DB_HOST = 'localhost'
DB_PASS = '12345'
DB_NAME = 'NTrailDB'
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

VERSION = '2.2'
API_SERVER_REQUEST_VERSION = 0


CACHE_TYPE = CACHE_TYPE_FULL_USE

# remote db
# DB_USER = 'postgres'
# DB_HOST = '51.79.69.179'
# DB_PASS = 'nef441'
# DB_NAME = 'socialsearch_db'
# DB_PORT = '5432'


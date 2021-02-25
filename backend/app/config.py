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

VERSION_MAJOR = 2
VERSION_MINOR = 1


def inc_version_build(filename: str) -> int:
    if not os.path.exists(filename):
        with open(filename, 'w') as file:
            file.write('0')
    with open(filename, 'r+') as build_file:
        content: str = build_file.read()
        if not content.isnumeric():
            logger.warning("Wrong build number file content, expected value")
            content = '0'
        build_file.seek(0)
        build_number = int(content) + 1
        build_file.write(str(build_number))
        return build_number


VERSION_BUILD = inc_version_build('data/build')

VERSION = f'{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}'
API_SERVER_REQUEST_VERSION = 0

# Способ кеширования
# CACHE_TYPE_FULL_USE - максимальное возможное
# TODO Add other ways to cache requests description
CACHE_TYPE = CACHE_TYPE_FULL_USE

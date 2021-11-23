import asyncpg

from worker.credentials.models import *

logger = logging.getLogger(__name__)

FILENAME = 'ig.txt'


async def main():
    with open(FILENAME, 'r') as f:
        lines = f.read().split('\n')

    lines = [
        line.strip() for line in lines if line.strip()
    ]
    await bind()

    for line in lines:
        account, cookie = line.split('|')
        login, password = account.split(':')
        cookies = dict([
            item.split('=', 1)
            for item in cookie.split(';')
        ])
        logger.debug('Account: %s: %s', login, password)
        try:
            await DBAccount.create(
                login=login,
                password=password,
                data={'cookie': cookies},
                service='ig'
            )
        except asyncpg.exceptions.UniqueViolationError:
            logger.info('Already exists')


if __name__ == '__main__':
    asyncio.run(main())

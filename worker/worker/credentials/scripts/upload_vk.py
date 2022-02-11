"""
Uploads tokens in vk-app.txt, vk-user.txt and vk-community.txt to DB
"""

import asyncpg

from worker.credentials.models import *
import sqlalchemy
from sqlalchemy.dialects.postgresql import insert


async def check_default_account(service) -> int:
    query = sqlalchemy.dialects.postgresql.insert(DBAccount).values(login='', password='', service=service) \
        .on_conflict_do_nothing()
    await db.all(query)
    return await DBAccount.select('id').where((DBAccount.service == service) & (DBAccount.login == '')).gino.scalar()


async def upload(type_):
    filename = f'vk-{type_}.txt'
    with open(filename, 'r') as f:
        lines = f.read().split('\n')

    tokens = [
        line.strip() for line in lines if line.strip()
    ]
    await bind()
    default_account_id = await check_default_account('vk')
    logger.info('default_account_id {}', default_account_id)
    for token in tokens:
        try:
            await DBAccess.create(token=token, account_id=default_account_id, type=type_)
        except asyncpg.exceptions.UniqueViolationError:
            logger.debug('Token already exists')


async def main():
    await upload('app')
    await upload('community')
    await upload('user')

if __name__ == '__main__':
    asyncio.run(main())

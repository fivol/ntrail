from worker.credentials.models import *
import psycopg2
import sqlalchemy
from sqlalchemy import create_engine
import asyncpg
import logging

FILENAME = 'vk-tokens-app.txt'


async def check_default_account(service):
    query = sqlalchemy.dialects.postgresql.insert(DBAccount).values(login='', password='', service=service).on_conflict_do_nothing()
    print(query.values(), query.params())
    async with db.acquire() as conn:
        await conn.raw_connection.execute(str(query), query.values())
    # await db.execute(insert(DBAccount).values(login='', password='', service=service).on_conflict_do_nothing())


logging.basicConfig(level=logging.DEBUG)


async def main():
    from sqlalchemy import MetaData, create_engine, Integer, String, Table, Column, DateTime, ForeignKey
    from sqlalchemy.dialects import postgresql

    engine = create_engine('postgres://postgres:password@localhost/postgres', echo=True)

    metadata = MetaData()
    network = Table('network', metadata,
                    Column('network_id', Integer, primary_key=True),
                    Column('name', String(100), nullable=False),
                    Column('created_at', DateTime, nullable=False),
                    Column('owner_id', Integer))

    user = Table('user', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('username', String),
                 Column('fullname', String))
    print((user.c.fullname == 'ad').compile(dialect=postgresql.dialect()))
    print((user.c.fullname == 'ad') & (user.c.id > 5))
    print((user.c.username == 'addward') | ((user.c.fullname == 'ad') & (user.c.id > 5)))

    return
    engine = create_engine('postgres://postgres:password@localhost/postgres')
    conn = engine.connect()
    conn.execute('create table if not exists test (id integer primary key, name varchar);')
    conn.execute('insert into test (id, name) values (%(id)s, %(name)s)', id=3, name='1234')
    cursor = conn.execute('select * from test')
    for line in cursor:
        print(dict(line))
    # conn = psycopg2.connect(database="ntrail-credentials", user="postgres", password="password", host='localhost', port=5432)
    # cursor = conn.cursor()
    # cursor.execute('select * from account')
    # print(cursor.fetchone())
    # print(cursor.fetchone())

    return
    with open(FILENAME, 'r') as f:
        lines = f.read().split('\n')

    tokens = [
        line.strip() for line in lines if line.strip()
    ]
    await bind()
    await check_default_account('vk')
    for token in tokens:
        await DBAccess.create(token=token)


if __name__ == '__main__':
    asyncio.run(main())

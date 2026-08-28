import asyncio

from models import db, Token


async def db_init():
    await db.set_bind('postgresql://postgres:example@db:5432/postgres')


async def init():
    await db_init()
    # await db.gino.drop_all()
    await db.gino.create_all()

    items = await db.all(Token.query)
    print(items)


if __name__ == '__main__':
    asyncio.run(init())


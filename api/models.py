from gino import Gino
import asyncio

from sqlalchemy import text

db = Gino()

db_url = 'postgresql://postgres:postgres@localhost:5432/ntrail_api'


class Token(db.Model):
    __tablename__ = 'tokens'
    token = db.Column(db.String, primary_key=True, server_default=text('gen_random_uuid()'))
    # Метод авторизации, например через вк, тг или через сайт NTrail
    auth_method = db.Column(db.String(20), nullable=False)
    # На данный момент просто vk id
    id = db.Column(db.Integer, unique=True, nullable=False)
    requests_count = db.Column(db.Integer, server_default=text('0'))
    requests_weight = db.Column(db.Float, server_default=text('0'))
    params = db.Column(db.JSON, server_default='{}')


async def drop_and_create():
    await db.set_bind(db_url)
    await db.gino.drop_all()
    await db.gino.create_all()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(drop_and_create())

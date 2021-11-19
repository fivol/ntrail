import asyncio

from gino import Gino
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy_mixins.timestamp import TimestampsMixin

db = Gino()


class DBAccount(db.Model, TimestampsMixin):
    __tablename__ = 'account'

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String, nullable=False)
    login = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    data = db.Column(JSONB, nullable=False, server_default="{}")
    access = relationship("DBAccess")

    _idx1 = db.Index('service_login_unique_index', 'service', 'login', unique=True)


class DBAccess(db.Model, TimestampsMixin):
    __tablename__ = 'access'

    id = db.Column(db.Integer(), primary_key=True)
    account_id = db.Column(db.Integer(), db.ForeignKey('account.id'), nullable=False)
    account = relationship("DBAccount")
    type = db.Column(db.String, nullable=True)
    status = db.Column(db.String, server_default='UNKNOWN')
    token = db.Column(db.String, nullable=True, unique=True)
    data = db.Column(JSONB, server_default="{}")


async def bind():
    await db.set_bind('postgresql://postgres:password@localhost:5432/ntrail-credentials')


async def main():
    await bind()
    await db.gino.drop_all()
    await db.gino.create_all()

if __name__ == '__main__':
    asyncio.run(main())

from gino import Gino
from sqlalchemy_mixins.timestamp import TimestampsMixin
from sqlalchemy_mixins.repr import ReprMixin
import asyncio

db = Gino()


class Token(TimestampsMixin, db.Model):
    __tablename__ = "tokens"
    id = db.Column(db.Integer, primary_key=True, index=True)
    service = db.Column(db.String(20), index=True)
    type = db.Column(db.String(20), index=True)
    token = db.Column(db.String(20), index=True)

    def __repr__(self):
        return f'Token(id={self.id}, service={self.service}, type={self.type})'


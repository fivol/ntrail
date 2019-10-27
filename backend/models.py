from peewee import *
import datetime
import random
import string
from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

from playhouse.postgres_ext import JSONField

db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASS,
                        host=DB_HOST, port=DB_PORT, autorollback=True)


class BaseModel(Model):
    class Meta:
        database = db


class PersonModel(BaseModel):
    hash = CharField(20)

    def __init__(self):
        super().__init__()
        self.hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


class UserModel(BaseModel):
    hash = CharField(20)

    def __init__(self):
        super().__init__()
        self.hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


class JsonModel(BaseModel):
    time = DateTimeField(default=datetime.datetime.now)
    target = CharField(30, default='')
    size = IntegerField(null=True)
    hash = CharField(20, unique=True, null=False)
    user = ForeignKeyField(UserModel, null=True)
    identity = JSONField()
    data = JSONField()


class ConfigModel(BaseModel):
    name = CharField(50, unique=True)
    value = CharField(100)


class QueryModel(BaseModel):
    time = DateTimeField(default=datetime.datetime.now)
    service = CharField(10, null=False)
    method = CharField(20, null=False)
    key = CharField(50, null=False)
    value = JSONField(null=False)
    params = JSONField(null=True)
    hash = CharField(20, unique=True, null=False)


def create_tables():
    with db:
        db.create_tables([ConfigModel, UserModel, PersonModel, JsonModel, QueryModel])


create_tables()

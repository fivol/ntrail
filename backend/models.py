from peewee import *
import datetime
from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

from playhouse.postgres_ext import JSONField

db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASS,
                        host=DB_HOST, port=DB_PORT, autorollback=True)


class BaseModel(Model):
    class Meta:
        database = db


class PersonModel(BaseModel):
    identity_hash = CharField(16)


class UserModel(BaseModel):
    login = CharField(50, null=False, unique=True)
    password = CharField(50, null=True, unique=False, index=True)
    status = CharField(50, null=False, unique=False)


class EntityModel(BaseModel):
    time = DateTimeField(default=datetime.datetime.now)
    target = CharField(30)
    size = IntegerField(null=True)
    user = ForeignKeyField(UserModel, null=True)
    identity = JSONField()
    identity_hash = CharField(16, unique=True, null=False)
    data = JSONField()


class FeatureModel(BaseModel):
    entity = ForeignKeyField(EntityModel, null=True)
    name = CharField(80, default='', null=False, index=True)
    value = FloatField(null=False, index=False, unique=False)

    class Meta:
        indexes = (
            (('entity', 'name'), True),  # create a unique
        )


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
    identity_hash = CharField(16, null=False, unique=True)


def create_tables():
    with db:
        db.create_tables([ConfigModel, UserModel, PersonModel,
                          EntityModel, QueryModel, FeatureModel])


create_tables()

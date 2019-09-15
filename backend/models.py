from peewee import *
import datetime


# DB_USER = 'postgres'
# DB_HOST = '51.79.69.179'
# DB_PASS = 'nef441'
# DB_NAME = 'socialsearch_db'
# DB_PORT = '5432'
# from playhouse.postgres_ext import JSONField
# db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASS,
#                         host=DB_HOST, port=DB_PORT)

from playhouse.sqlite_ext import JSONField
db = SqliteDatabase('socialsearch.db')


class BaseModel(Model):
    class Meta:
        database = db


class CommunityData(BaseModel):
    time = DateTimeField(default=datetime.datetime.now)
    target = CharField(default='test')
    user = IntegerField(null=True)
    data = JSONField()


def create_tables():
    with db:
        db.create_tables([CommunityData])


create_tables()

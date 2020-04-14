# noinspection DuplicatedCode
from peewee import *

from NodeConfig import NodeConfig

NodeConfig.check_dir()
node_db: SqliteDatabase = SqliteDatabase('.config/db.sqlite')


class BaseModel(Model):
    class Meta:
        database = node_db


class ClientModel(BaseModel):
    identity = CharField(max_length=50, primary_key=True, unique=True)
    public_key = CharField(max_length=450, unique=True)
    last_seen = BigIntegerField()


node_db.create_tables([ClientModel])

from fastapi import FastAPI
from db import db, db_init
from models import Token


app = FastAPI(on_startup=[db_init])


@app.get("/")
def version():
    return '1.0.0'


@app.get("/vk/user/")
async def read_item():
    return [item.to_dict() for item in await db.all(Token.query)]

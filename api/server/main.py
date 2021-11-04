import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from server.config import config
from server.models import db, db_url
from server.routes.vk import vk
from server.routes import auth
from server.plugin.register import register_plugins
from worker import Engine

logger = logging.getLogger('main')

app = FastAPI(
    debug=config.DEBUG,
    title='NTrail API',
    version=config.get('VERSION'),
    description='[Читать описание API на Gitbook](https://borisoffficial.gitbook.io/ntrail-api/). '
                'Там подробно про каждый метод, лимиты, получение токена и т.д.'
)

engine: Engine


@app.on_event('shutdown')
def shutdown_event():
    print('shutdown')
    engine.stop()


@app.on_event('startup')
def startup_event():
    global engine
    engine = Engine(caching=config.bool('CACHING'))


app.include_router(vk.router)
app.include_router(auth.router)

register_plugins()


@app.on_event("startup")
async def startup_event():
    pass
    # await db.set_bind(db_url)


@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def index():
    return RedirectResponse("/version/")


@app.get('/version/', response_model=str)
async def version():
    """Текущая версия API"""
    return config.get('VERSION')

import asyncio
import logging
import time

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse

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


# https://github.com/tiangolo/fastapi/issues/1752
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """If query is too long, stop it with 504"""
    start_time = time.time()
    try:
        return await asyncio.wait_for(call_next(request), timeout=config.int('REQUESTS_TIMEOUT'))
    except asyncio.TimeoutError:
        process_time = time.time() - start_time
        return JSONResponse({'detail': 'Request processing time excedeed limit',
                             'processing_time': process_time},
                            status_code=status.HTTP_504_GATEWAY_TIMEOUT)


@app.on_event('shutdown')
async def shutdown_event():
    await engine.stop()


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


@app.get('/config/', response_model=dict)
async def get_config():
    return {
        'DEBUG': config.get('DEBUG'),
        'CACHING': config.get('CACHING'),
    }


import asyncio
import logging
import time

import aiohttp
from fastapi import FastAPI, Request, status, Response
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse

from server.config import config
from server.routes.vk import vk
from server.routes.ig import ig
from server.routes import auth
from server.plugin.register import register_plugins
from worker import Engine
from worker.ctx import get_context
from loguru import logger


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
        return JSONResponse({'detail': 'Request processing time exceeded limit',
                             'processing_time': process_time},
                            status_code=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception:
        logger.exception('SOME BIG PROBLEM')
        return JSONResponse({'detail': 'Request exception'},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.on_event('shutdown')
async def shutdown_event():
    await engine.stop()


@app.on_event('startup')
async def startup_event():
    logger.info('Server started')
    global engine
    engine = Engine(caching=config.bool('CACHING'), access_safe_mode=config.get('access_factory.safe_mode', True))
    await engine.start()


app.include_router(vk.router)
app.include_router(ig.router)
app.include_router(auth.router)

register_plugins()


@app.on_event("startup")
async def startup_event():
    # asyncio.create_task(alive_check_daemon())
    pass
    # await db.set_bind(db_url)


@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def index():
    return RedirectResponse("/version/")


@app.get('/version/')
async def version():
    """Текущая версия API"""
    return Response(content=config.get('VERSION'))


@app.get('/config/', response_model=dict)
async def get_config():
    ctx = get_context()
    return {
        'DEBUG': config.get('DEBUG'),
        'CACHING': config.get('CACHING'),
        'context': repr(ctx)
    }


async def alive_check_daemon():
    while True:
        await asyncio.sleep(config.check_alive_interval)
        logger.debug('CHECK ALIVE')
        timeout = aiohttp.ClientTimeout(total=config.check_alive_limit_timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f'{config.BASE_URL}/vk/user/?user=id245089915&options=user') as response:
                    status_code = response.status
                    if int(status_code / 100) != 2:
                        logger.error('It seems server failed')
                    logger.debug('SERVER ALIVE')
        except:
            logger.exception('SERVER CHECK TIMEOUT EXCEEDED')


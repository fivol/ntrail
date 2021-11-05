import logging
import aioredis
import json

from worker.config import config
from worker.ctx import get_context


logger = logging.getLogger()

ctx = get_context()


def get_redis():
    return aioredis.from_url(
        config.redis_url, encoding="utf-8", decode_responses=True
    )


def init():
    ctx.redis = get_redis()
    ctx.set_default('caching_available', None)
    ctx.set_default('caching', True)
    if ctx.caching:
        logger.info('Caching enabled')
    else:
        logger.info('Caching disabled')


def redis_cache(method):
    async def _wrapper(*args, **kwargs):
        if not ctx.caching or ctx.caching_available is False:
            return await method(*args, **kwargs)
        try:
            call_encoded = f'{method.__name__}-{args}-{kwargs}'
            cached_result = await ctx.redis.get(call_encoded)
            ctx.caching_available = True

            if cached_result is None:
                result = await method(*args, **kwargs)
                await ctx.redis.set(call_encoded, json.dumps(result))
                logger.debug('Cache miss')
                return result
            else:
                logger.debug('Cache hit')
                return json.loads(cached_result)
        except ConnectionError:
            if ctx.caching_available is None:
                logger.warning('Redis ConnectionError')
            ctx.caching_available = False

        return await method(*args, **kwargs)
    return _wrapper

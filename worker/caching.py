import asyncio
import logging
from functools import wraps
import aioredis
import json

logger = logging.getLogger('cache')


def get_redis():
    return aioredis.from_url(
        "redis://localhost", encoding="utf-8", decode_responses=True
    )


_redis = get_redis()
_caching_available = True


def cache_with_redis(method):
    async def _wrapper(*args, **kwargs):
        global _caching_available
        if not _caching_available:
            return await method(*args, **kwargs)
        try:
            call_encoded = f'{method.__name__}-{args}-{kwargs}'
            cached_result = await _redis.get(call_encoded)
            if cached_result is None:
                result = await method(*args, **kwargs)
                await _redis.set(call_encoded, json.dumps(result))
                logger.debug('Cache miss')
                return result
            else:
                logger.debug('Cache hit')
                return json.loads(cached_result)
        except ConnectionError:
            _caching_available = False
            logger.warning('Redis ConnectionError')

        return await method(*args, **kwargs)
    return _wrapper

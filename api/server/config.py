import sys

import aiohttp
from bestconfig import Config
from loguru import logger


logger.remove()
logger.add(sys.stdout, serialize=True)

config = Config('local-config.yml', exclude=['env_file'])

config.assert_contains('DEBUG')


async def send_alarmer_message(text):
    async with aiohttp.ClientSession() as session:
        url = f'https://alarmerbot.ru/?key={config.ALARMER_KEY}&message={text}'
        await session.get(url)


async def error_logger(msg):
    message = f"NTrail API error: {msg.record['message'].lower()}"
    try:
        await send_alarmer_message(message)
    except:
        logger.exception('Failed to alarm')


logger.add(error_logger, level='ERROR', format='{message}')

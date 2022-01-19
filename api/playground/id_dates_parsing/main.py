import asyncio
import logging
from contextlib import suppress
from datetime import datetime
from pprint import pprint

from tqdm import tqdm, trange

from core import VKUser, VKCommunity
from server.plugin.register import register_plugins
from server.plugin.plugin_manager import PluginManager
from worker import Engine
from worker import VKMethods

register_plugins()

logger = logging.getLogger()


async def first_date(user_id) -> datetime:
    user = VKUser(user_id)
    first_profile_photo = None
    first_post = None
    with suppress(Exception):
        first_profile_photo = (await user.profile_photos())[-1]
    with suppress(Exception):
        first_post = (await user.posts())[-1]
    if first_post and first_profile_photo:
        return min(await first_post.date(), await first_profile_photo.date())
    if first_post:
        return await first_post.date()
    if first_profile_photo:
        return await first_profile_photo.date()
    raise ValueError


async def get_pages_dates(ids):
    dates = await asyncio.gather(*[
        first_date(i) for i in ids
    ], return_exceptions=True)
    results = [
        (i, date) for i, date in zip(ids, dates) if isinstance(date, datetime)
    ]
    print(len(results))
    return results


async def main():
    logging.disable(logging.ERROR)
    start_from = 228491901
    max_id = int(1e6 * 680)  # 10 M

    step = 1000

    bunch_size = 500
    for i in trange(start_from, max_id, step * bunch_size):
        await asyncio.sleep(0.01)
        continue
        dates = await get_pages_dates(list(range(i, i + bunch_size * step, step)))
        if not dates:
            continue
        with open('.data/id_dates_posts-profile.txt', 'a') as f:
            lines = [f'{id} {date.strftime("%d.%m.%Y")}' for id, date in dates]
            f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    with Engine(caching=False):
        asyncio.get_event_loop().run_until_complete(main())

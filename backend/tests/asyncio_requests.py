import asyncio
import aiohttp
import logging

logging.getLogger('asyncio').setLevel(logging.CRITICAL)

async def get(url):
    response = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response = resp.status

    return response

async def run(url, count):
    tasks = [get(url) for i in range(count)]
    return await asyncio.gather(*tasks)

async def f():
    async def g():
        await asyncio.sleep(0.6)
    await asyncio.gather(g(), g(), g())
    

if __name__ == "__main__":
    import time
    s = time.perf_counter()
    res = asyncio.run(run('https://www.instagram.com/fivol5/?__a=1', 1000))
    #res = asyncio.run(f())
    print(res)
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")

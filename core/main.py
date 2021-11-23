import asyncio
import warnings
import core.config # noqa
from worker import Engine

warnings.simplefilter('ignore')


async def main():
    async with Engine(caching=True):
        pass


if __name__ == '__main__':
    asyncio.run(main())

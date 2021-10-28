import asyncio
from aiovk import TokenSession, API

# https://github.com/Fahreeve/aiovk


async def main():
    async with TokenSession(access_token='7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1') as ses:
        ses.API_VERSION = '5.103'
        api = API(ses)
        print(await api.users.get(user_ids=1))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


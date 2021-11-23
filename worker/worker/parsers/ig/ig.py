from igramscraper.instagram import Instagram
from worker.credentials.access import AccessModel
from worker.parsers.layers import items_getter
from worker.parsers.parser import BaseParser
from worker.session.session_manager import SessionManager
from worker.session.session_state import SessionState


class IgApiSession(SessionState):
    def __init__(self, *args, **kwargs):
        self.__ig_session = None
        super().__init__(*args, **kwargs)

    def create(self, access: AccessModel):
        self.__ig_session = Instagram(cookie=access.data['cookie'])
        return self.__ig_session

    async def close(self):
        pass

    def handle_error(self, exc_type, exc_val, exc_tb):
        pass


class IgMethods(BaseParser):
    _api = SessionManager(key_type='ig', controller=IgApiSession, requests_delay_min=10, requests_delay_max=30)

    @classmethod
    async def stop(cls):
        await cls._api.stop()

    @classmethod
    async def account(cls, account_id):
        async with await cls._api.get() as api:
            return await api.get_account(account_id)

    @classmethod
    async def resolve(cls, username):
        async with await cls._api.get() as api:
            return await api.resolve_username(username)

    @classmethod
    @items_getter
    async def followers(cls, account_id):
        async with await cls._api.get() as api:
            return await api.get_followers(account_id, count=50)

    @classmethod
    @items_getter
    async def following(cls, account_id):
        async with await cls._api.get() as api:
            return await api.get_following(account_id, count=20)

    @classmethod
    async def test(cls, arg):
        async with await cls._api.get() as api:
            return await api.test(arg)


"""
get_account_json_link огромный массив в нужными данными и не только по username
"""
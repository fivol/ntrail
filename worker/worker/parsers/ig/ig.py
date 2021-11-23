from worker.instagramscraper.instagram import Instagram
from worker.credentials.access import AccessModel
from worker.helpers.caching import redis_cache
from worker.helpers.layers import method_logger
from worker.helpers.methods_injector import inject_methods_wrappers, ignore_injection
from worker.helpers.tools import decorate
from worker.parsers.ig.layers import paging_iterator
from worker.parsers.layers import items_getter, mapped_method, reliable_call
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


@inject_methods_wrappers(method_logger(name=__name__), redis_cache, mapped_method)
class IGMethods(BaseParser):
    _api = SessionManager(key_type='ig', controller=IgApiSession, requests_delay_min=10, requests_delay_max=30)

    @classmethod
    @ignore_injection
    async def stop(cls):
        await cls._api.stop()

    @classmethod
    @decorate(reliable_call)
    async def account(cls, account_id):
        async with await cls._api.get() as api:
            return await api.get_account(account_id)

    @classmethod
    @decorate(reliable_call)
    async def resolve(cls, username):
        async with await cls._api.get() as api:
            return await api.resolve_username(username)

    @classmethod
    @decorate(reliable_call, items_getter, paging_iterator(50))
    async def followers(cls, account_id, count, end_cursor=''):
        async with await cls._api.get() as api:
            return await api.get_followers(account_id, count=count, end_cursor=end_cursor)

    @classmethod
    @decorate(reliable_call, items_getter, paging_iterator(49))
    async def following(cls, account_id, count, end_cursor=''):
        async with await cls._api.get() as api:
            return await api.get_following(account_id, count=count, end_cursor=end_cursor)

    @classmethod
    async def test(cls, arg):
        async with await cls._api.get() as api:
            return await api.get_followers(arg, count=1)


"""
get_account_json_link огромный массив в нужными данными и не только по username
"""
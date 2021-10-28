import asyncio
from random import randint

from aiovk import TokenSession, API
from collections import deque
from time import time

# https://github.com/Fahreeve/aiovk

class CredentialsServerApi:
    tokens = [
        '7c5bcbdb7c5bcbdb7c5bcbdb9b7c37ff7177c5b7c5bcbdb211516ab57c448a13e033bb1'
    ]

    @classmethod
    def get_tokens(cls, count: int):
        # TODO Call Credentials server
        send_tokens = cls.tokens[:count]
        cls.tokens = cls.tokens[count:]
        return send_tokens

    @classmethod
    def return_tokens(cls, tokens):
        # TODO Call Credentials server and return tokens
        cls.tokens += tokens


class TokenState:
    """
    Описывает вызов токена, время обращения к нему, состояние и прочее
    """
    def __init__(self, token: str):
        self.token = token
        self.last_used_time = None
        # Если словил limit, это значение указывает, когда снова будет в строю (если известно)
        self.will_ready_time = None
        self.status = None
        self._expire_time = None

    def is_ready(self):
        # TODO
        return not self.is_expired()

    def is_expired(self):
        return self._expire_time and time() > self._expire_time


class RequestException(Exception):
    pass

class NoTokenAvailableException(RequestException):
    pass


class ApiLimitException(RequestException):
    pass


class VkSessionManager:
    """
    Поддерживает сессии для обращения к endpoint-ам вк
    """

    def __init__(self, *args, **kwargs):
        self._all_tokens = set()
        self._active_queue = deque()
        self._waiting_queue = set()

    def get(self):
        return API(session=self._get_session())

    def release(self, api, status):
        pass

    @staticmethod
    def _create_session(token):
        session = TokenSession(access_token=token)
        session.API_VERSION = '5.103'
        return session

    def _check_waiting_queue(self):
        while self._waiting_queue:
            revive_time, token = self._waiting_queue.pop()
            if revive_time < time():
                self._active_queue.append(token)
            else:
                self._waiting_queue.add((revive_time, token))
                break

    def __filter_new_tokens(self, tokens):
        new_tokens = list(filter(lambda t: t not in self._all_tokens, tokens))
        if len(new_tokens) != tokens:
            raise RuntimeWarning('Credentials server do not work properly')
        return new_tokens

    def __add_new_tokens(self, tokens):
        for token in tokens:
            self._all_tokens.add(token)
            # TODO tokens can be not plain string, for example can contain revive time
            self._active_queue.appendleft(TokenState(token))

    def _receive_tokens(self):
        count = len(self._active_queue)
        tokens = self.__filter_new_tokens(CredentialsServerApi.get_tokens(count))
        self.__add_new_tokens(tokens)
        return tokens

    def _return_expired(self, receive=False):
        if receive:
            self._receive_tokens()

    def _get_session(self):
        while True:
            if not len(self._active_queue) or not randint(0, 10):
                self._check_waiting_queue()

            if not self._active_queue:
                if self._receive_tokens():
                    continue
                raise NoTokenAvailableException()

            token = self._active_queue.popleft()
            if not token.is_ready():
                self._active_queue.appendleft(token)
                if token.is_expired():
                    self._return_expired()
                    continue
                if self._receive_tokens():
                    continue
                raise ApiLimitException()

            return token


class VkMethods:
    user_api = VkSessionManager(type='vk.user.token')
    app_api = VkSessionManager(type='vk.app.token')
    # TODO Add ability to combine managers in context manager
    # To call any available api for example

    @classmethod
    async def _wrapper(cls):
        pass

    @classmethod
    async def friends(cls, user_id):
        async with cls.user_api.get() as api:
            return await api.users.get(user_ids=user_id)


async def main():
    pass


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


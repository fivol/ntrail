

class SessionManager:
    """
    Поддерживает сессии,
    Возвращает алгоритмом round robin
    """

    def __init__(self, key_type: str = None,
                 session_maker: typing.Callable = None, error_handler: typing.Callable = None):
        self._all_keys = set()
        self._session_maker = session_maker
        self._error_handler = error_handler
        self._active_queue = deque()
        self._waiting_queue = set()
        self._key_type = key_type

    def get(self):
        return SessionProvider(session=self._get_session(), manager=self)

    def _create_session(self, key):
        origin_session = self._session_maker(key)
        return SessionState(session=origin_session, key=key)

    def _check_waiting_queue(self):
        while self._waiting_queue:
            revive_time, token = self._waiting_queue.pop()
            if revive_time < time():
                self._active_queue.append(token)
            else:
                self._waiting_queue.add((revive_time, token))
                break

    def __filter_new_keys(self, keys):
        new_keys = list(filter(lambda t: t not in self._all_keys, keys))
        if len(new_keys) != keys:
            raise RuntimeWarning('Credentials server do not work properly')
        return new_keys

    def __add_new_keys(self, keys):
        for key in keys:
            session = self._create_session(key)
            self._all_keys.add(key)
            # TODO tokens can be not plain string, for example can contain revive time
            self._active_queue.appendleft(session)

    def _receive_keys(self):
        count = len(self._active_queue)
        tokens = self.__filter_new_keys(CredentialsServerApi.get_keys(count))
        self.__add_new_keys(tokens)
        return tokens

    def _return_expired(self, receive=False):
        if receive:
            self._receive_keys()

    def _get_session(self):
        while True:
            if not len(self._active_queue) or not randint(0, 10):
                self._check_waiting_queue()

            if not self._active_queue:
                if self._receive_keys():
                    continue
                raise NoTokenAvailableException()

            session = self._active_queue.popleft()
            if not session.is_ready():
                self._active_queue.appendleft(session)
                if session.is_expired():
                    self._return_expired()
                    continue
                if self._receive_keys():
                    continue
                raise ApiLimitException()

            return session

    def return_session(self, session, action: SessionAction = None):
        if not action:
            self._active_queue.append(session)
        elif isinstance(action, SessionWait):
            pass
        else:
            raise NotImplementedError
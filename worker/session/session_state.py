from time import time


class SessionState:
    """
    Описывает вызов токена, время обращения к нему, состояние и прочее
    """

    def __init__(self, session, key=None):
        self.key = key
        self.session = session
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

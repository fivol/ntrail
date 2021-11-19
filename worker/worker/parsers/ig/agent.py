import logging
import time

from worker.parsers.ig.instagramlib import WebAgentAccount, InternetException, UnexpectedResponse
from worker.parsers.ig.state import *

logger = logging.getLogger()


class InstAgent:
    logging = False

    def __init__(self, username, password=None):
        self.username = username
        self.password = password
        self.valid = None
        self.dead = False
        self.using = False
        self.authorized = False
        self.last_request_time = 0
        self.requests_count = 0
        self.last_429_check_time = 0
        self.first_429_request_time = 0
        self.valid = self.is_valid()
        self.agent = WebAgentAccount(username, logger=logger if self.logging else None)

        self.auth()

    def __str__(self):
        return f'{self.username} {self.status()}'

    @staticmethod
    def is_valid():
        return True

    def auth(self):
        try:
            self.get().auth(self.password)
            self.authorized = True
            self.valid = True
        except InternetException as e:
            self.valid = False
            logger.error('Inst Agent AUTH FAIL! InternetException %s %s', self, e)
        except UnexpectedResponse as e:
            self.valid = False
            logger.error('Inst Agent AUTH FAIL! UnexpectedResponse. %s %s', self, e)

    def reload(self):
        pass

    def get(self):
        return self.agent

    def book(self):
        self.using = True

    def free(self):
        self.using = False

    def need_wait(self):
        return time.time() - self.first_429_request_time < 10 * 60

    def status(self):
        if not self.authorized and self.valid is None:
            return STATUS_WAIT_AGENT
        if self.dead or self.valid is False:
            return STATUS_DEAD_AGENT
        if self.using:
            return STATUS_USING_AGENT
        if self.need_wait():
            return STATUS_WAIT_AGENT
        return STATUS_GOOD_AGENT

    def request(self, func_name, *args, **kwargs):
        request_status = None
        request_result = REQUEST_STATUS_FAIL
        self.book()
        try:
            logger.debug('* Inst api call: {}, agent: {}'.format(func_name, self.username))
            self.last_request_time = time.time()
            request_result = getattr(self.get(), func_name)(*args, **kwargs)
            request_status = REQUEST_STATUS_OK
        except InternetException as e:
            if hasattr(e, 'response'):
                code = e.response.status_code
                if code == 429:
                    self.first_429_request_time = time.time()
                if code == 404:
                    self.valid = False
            else:
                raise e
        except UnexpectedResponse as e:
            logger.critical('Instagram UnexpectedResponse. %s, %s', args, kwargs)
            raise e
        except TypeError as e:
            if 'NoneType' in str(e):
                request_status = REQUEST_STATUS_OK
                request_result = REQUEST_ERROR_404
                logger.exception('404 %s %s %s', func_name, args, kwargs)
            else:
                raise e

        self.free()
        return request_status, request_result
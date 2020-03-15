import time
from instagram import Account, Media, WebAgent, WebAgentAccount, HasMediaElement
from instagram.exceptions import HTTPError, InternetException, UnexpectedResponse
from app_data import inst_accounts_data
from glbal import logger
from tools import get, ThreadResult, sequential_start, MemoryCache
import random

REQUEST_ERROR_404 = 'REQUEST_ERROR_404'

STATUS_GOOD_AGENT = 'STATUS_GOOD_AGENT'
STATUS_WAIT_AGENT = 'STATUS_WAIT_AGENT'
STATUS_DEAD_AGENT = 'STATUS_DEAD_AGENT'
STATUS_USING_AGENT = 'STATUS_USING_AGENT'

REQUEST_STATUS_OK = 'REQUEST_STATUS_OK'
REQUEST_STATUS_FAIL = 'REQUEST_STATUS_FAIL'

dead_agents = set()

try:
    with open('../data/dead_agents', 'r') as f:
        globals()['dead_agents'] = set(f.read().split(','))
except:
    logger.debug('dead_agents file not found')
    with open('../data/dead_agents', 'w') as f:
        f.write('')


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

    def is_valid(self):
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


class InstRequest:
    force_requests = False
    good_agents = set()
    wait_agents = set()
    active_agents = set()
    used_agents = set()
    last_agent_review_time = 0

    @classmethod
    def print_stat(cls):
        print('Good agents count:', len(cls.good_agents))
        print('Wait agents count:', len(cls.wait_agents))
        print('Active agents count:', len(cls.active_agents))
        print('Used agents count:', len(cls.used_agents))
        print('Last_agent_review_time:', time.time() - cls.last_agent_review_time)
        print('Force requests:', cls.force_requests)

    @classmethod
    @sequential_start
    def review_wait_agents(cls):
        if time.time() - cls.last_agent_review_time < 20:
            return

        to_good = set()
        to_dead = set()
        for agent in cls.wait_agents:
            if agent.status() == STATUS_GOOD_AGENT:
                to_good.add(agent)
            if agent.status() == STATUS_DEAD_AGENT:
                logger.warning('Found dead agent in WAIT LIST:', agent)
                to_dead.add(agent)

        cls.wait_agents -= to_dead
        cls.wait_agents -= to_good
        cls.good_agents |= to_good

        cls.last_agent_review_time = time.time()

    @classmethod
    @sequential_start
    def check_agent(cls):
        cls.review_wait_agents()
        if cls.good_agents:
            agent = next(iter(InstRequest.good_agents))
            cls.good_agents.remove(agent)
            return agent
        return None

    @classmethod
    def get_agent(cls):
        while True:
            agent = cls.check_agent()
            if agent:
                return agent

            new_agent = cls.create_agent()
            if isinstance(new_agent, InstAgent):
                return new_agent
            else:
                sleep_time = 1 + random.random()
                # logger.warning('Empty list of agents. Wait %s seconds', sleep_time)
                time.sleep(sleep_time)

    @classmethod
    def start_agents(cls, count=-1):
        while count != 0:
            count -= 1
            agent = cls.create_agent()
            if not agent:
                return

    @classmethod
    @sequential_start
    def process_agent(cls, agent):
        agent_status = agent.status()
        if agent_status == STATUS_DEAD_AGENT:
            with open('../data/dead_agents', 'a') as f:
                f.write(agent.username + ',')
            logger.error('DEAD agent: %s', agent)
            if agent in cls.wait_agents:
                cls.wait_agents.remove(agent)
            if agent in cls.good_agents:
                cls.good_agents.remove(agent)
            if agent in cls.active_agents:
                cls.active_agents.remove(agent)

        elif agent_status == STATUS_WAIT_AGENT:
            if agent in cls.good_agents:
                cls.good_agents.remove(agent)
            cls.wait_agents.add(agent)

        elif agent_status == STATUS_GOOD_AGENT:
            if agent in cls.wait_agents:
                cls.wait_agents.remove(agent)
            cls.good_agents.add(agent)

        else:
            logger.critical('Process agent find unknown status. %s', agent)
            raise Exception()

    @classmethod
    @sequential_start
    def create_agent(cls):
        for username, password in inst_accounts_data:
            if username not in dead_agents and username not in cls.used_agents:
                if username in get('inst_agents'):
                    logger.debug('Add inst agent from cache: {}'.format(username))
                    new_agent = get('inst_agents')[username]
                    new_agent.reload()
                else:
                    logger.debug('Add inst agent: {}'.format(username))
                    new_agent = InstAgent(username, password)
                    get('inst_agents')[username] = new_agent
                    cls.process_agent(new_agent)

                cls.used_agents.add(username)
                if new_agent.status() is STATUS_DEAD_AGENT:
                    continue

                cls.active_agents.add(new_agent)
                return new_agent
        return None

    def make_request(self, func_name, *args, **kwargs):
        while True:
            agent = self.get_agent()
            request_status, request_result = agent.request(func_name, *args, **kwargs)
            self.process_agent(agent)
            if request_status is REQUEST_STATUS_OK:
                return request_result
            if request_status is REQUEST_STATUS_FAIL:
                if agent.status() not in [STATUS_WAIT_AGENT, STATUS_DEAD_AGENT, STATUS_GOOD_AGENT]:
                    logger.critical('AAA! Unintended agent status. %s', agent)
                    raise Exception()


class IGAPI(InstRequest):

    def repeat_load(self, func_name, count, data=None):
        assert isinstance(func_name, str)
        default_limit = 100
        limit = data.get('limit', default_limit)
        data['limit'] = limit
        data['count'] = limit
        if count < -1 or count == 0:
            raise ValueError('Wrong count value')
        result = self.make_request(func_name, **data)
        if not result:
            return None
        if result is REQUEST_ERROR_404:
            logger.warning('Repeat load func: %s, data: %s 404 ERROR', func_name, data)
            return []
        try:
            items, pointer = result
            count -= limit
        except ValueError:
            logger.error('Too many values to unpack. First request: %s', result)
            return []
        while pointer and (count == -1 or count > 0):
            result = self.make_request(func_name,
                                       **data,
                                       pointer=pointer)
            try:
                items_, pointer = result
                count -= len(items_)
                items += items_
            except ValueError:
                logger.error('Too many values to unpack: %s', result)

        return items

    def get_media(self, obj, full=False):
        assert isinstance(obj, HasMediaElement)
        element = (str(obj), full)
        full_element = (str(obj), True)
        if self.force_requests or \
                (element not in get('obj_media') and
                 full_element not in get('obj_media')):
            response = self.make_request('get_media', obj)
            if response is REQUEST_ERROR_404:
                get('obj_media')[element] = None
            else:
                get('obj_media')[element] = obj
        if element in get('obj_media'):
            return get('obj_media')[element]
        return get('obj_media')[full_element]

    def get_followers(self, username, count=-1, **kwargs):
        assert isinstance(username, str)
        if username not in get('users_followers') or self.force_requests:
            data = {
                'account': Account(username),
                **kwargs
            }
            nodes = self.repeat_load('get_followers', count, data=data)
            if not nodes:
                nodes = []
            if nodes:
                for node in nodes:
                    get('obj_media')[(node.username, False)] = node
            get('users_followers')[username] = [node.username for node in nodes]
        return get('users_followers')[username]

    def get_follows(self, username, count=-1, **kwargs):
        assert isinstance(username, str)
        if self.force_requests or username not in get('users_follows'):
            data = {
                'account': Account(username),
                **kwargs
            }
            nodes = self.repeat_load('get_follows', count, data=data)
            if nodes:
                for node in nodes:
                    get('obj_media')[(node.username, False)] = node
            if not nodes:
                nodes = []
            get('users_follows')[username] = [node.username for node in nodes]
        return get('users_follows')[username]

    def get_objects_medias(self, objects, **kwargs):
        threads = [
            ThreadResult(target=self.get_media, args=(obj,), kwargs=kwargs)
            for obj in objects
        ]
        return [thread.execute() for thread in threads]

    def get_users_followers(self, users, count=300, **kwargs):
        threads = [
            ThreadResult(target=self.get_followers,
                         args=(username,),
                         kwargs={'count': count, **kwargs})
            for username in users
        ]
        return [thread.execute() for thread in threads]

    def get_users_follows(self, users, count=300, **kwargs):
        threads = [
            ThreadResult(target=self.get_follows,
                         args=(username,),
                         kwargs={'count': count, **kwargs})
            for username in users
        ]
        return [thread.execute() for thread in threads]


MemoryCache.load_memory()

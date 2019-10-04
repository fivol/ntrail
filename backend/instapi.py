import time
from instagram import Account, Media, WebAgent, WebAgentAccount
from instagram.exceptions import HTTPError, InternetException, UnexpectedResponse
from queue import Queue
from threading import Thread
from app_data import inst_accounts_data
from glbal import logger
import random
import pickle


ACCOUNT_DOES_NOT_EXIST = 'ACCOUNT_DOES_NOT_EXIST'
INTERNET_EXCEPTION = 'INTERNET_EXCEPTION'


class InstRequest:
    force_requests = False
    agents_queue = Queue()
    active_agents = set()

    def get_agent(self, func_name=None):
        if func_name in ['get_media']:
            return WebAgent(), 0
        if agents_queue.empty():
            agent = self.create_agent()
            if agent:
                agents_queue.put((agent, time.time() - 10))
            else:
                logger.warning('EMPTY AGENTS LIST')
                time.sleep(1)
                return self.get_agent()

        agent, last_call_time = agents_queue.get()
        if time.time() - last_call_time < 2:
            new_agent = self.create_agent()
            if new_agent:
                agents_queue.put((new_agent, time.time() - 10))
            else:
                logger.warning('NEED MORE INST AGENTS!')

            wait_time = max(0, 1 + random.random() * 2 - (time.time() - last_call_time))
            if wait_time:
                logger.info('SLEEP {} seconds'.format(wait_time))
                time.sleep(wait_time)
        return agent, last_call_time

    @staticmethod
    def return_agent(agent):
        if agent.__class__ != WebAgent().__class__:
            agents_queue.put((agent, time.time()))

    def start_agents(self, count=-1):
        while count != 0:
            count -= 1
            agent = self.create_agent()
            if not agent:
                return
            agents_queue.put((agent, time.time() - 5))

    @staticmethod
    def create_agent():
        for username, password in inst_accounts_data:
            if username not in active_agents:
                try:
                    if username in inst_agents:
                        logger.debug('Add inst agent from cache: {}'.format(username))
                        new_agent = inst_agents[username]
                    else:
                        logger.debug('Add inst agent: {}'.format(username))
                        new_agent = WebAgentAccount(username)
                        new_agent.auth(password)
                        inst_agents[username] = new_agent
                    active_agents.add(username)
                    return new_agent
                except InternetException as e:
                    inst_agents[username] = None
                    logger.error('Inst Agent auth fail! InternetException %s %s', username, e)
                except UnexpectedResponse as e:
                    inst_agents[username] = None
                    logger.error('Inst Agent FAIL UnexpectedResponse. %s', username, e)

        return None

    def make_request(self, func_name, *args, **kwargs):
        agent, last_call_time = self.get_agent(func_name)
        try:
            logger.debug('* Inst api call: {}, agent: {}'.format(func_name, agent))
            result = getattr(agent, func_name)(*args, **kwargs)
            self.return_agent(agent)
            return result
        except InternetException as e:
            if hasattr(e, 'response'):
                code = e.response.status_code
                if code == 429:
                    t = 2 + random.random() * 3
                    logger.error('[429] Error. Kill agent %s. Sleep %s seconds', agent, t)
                    time.sleep(t)
                    return self.make_request(func_name, *args, **kwargs)
                if code == 404:
                    self.return_agent(agent)
                    logger.error('[404] Object not found')
                    return ACCOUNT_DOES_NOT_EXIST
            else:
                logger.critical('InternetException %s', e)
                return INTERNET_EXCEPTION
            # raise e
        except UnexpectedResponse as e:
            logger.critical('Instagram UnexpectedResponse. %s, %s', args, kwargs)
            raise e
        except TypeError as e:
            if 'HasMediaElement' in str(e):
                logger.warning('Instagram HasMediaElement Error: %s, %s', args, kwargs)
                return None
            raise e


class ThreadResult:
    def __init__(self, target=None, args=None, kwargs=None):
        self.result = None
        if not args:
            args = []
        if not kwargs:
            kwargs = {}

        def saver_func(*args_, **kwargs_):
            self.result = target(*args_, **kwargs_)

        self.thread = Thread(target=saver_func, args=args, kwargs=kwargs)
        self.thread.start()

    def execute(self):
        self.thread.join()
        return self.result


class InstAPI(InstRequest):
    @staticmethod
    def clear_memory():
        global agents_queue, obj_media, users_followers, users_follows, inst_agents, active_agents
        agents_queue = Queue()
        active_agents = set()
        inst_agents = {}
        obj_media = {}
        users_follows = {}
        users_followers = {}

    def repeat_load(self, func_name, count, limit, data=None):
        data['count'] = limit
        if count < -1 or count == 0:
            raise ValueError('Wrong count value')
        result = self.make_request(func_name, **data)
        if not result:
            return None
        items, pointer = result
        count -= limit
        while pointer and (count == -1 or count > 0):
            result = self.make_request(func_name,
                                       **data,
                                       pointer=pointer)
            if result is INTERNET_EXCEPTION:
                return []
            items_, pointer = result
            count -= limit
            items += items_

        return items

    def get_followers(self, username, count=-1, limit=100):
        if username not in users_followers or self.force_requests:
            data = {
                'account': Account(username)
            }
            nodes = self.repeat_load('get_followers', count, limit=limit, data=data)
            if nodes:
                for node in nodes:
                    obj_media[node.username] = node
            users_followers[username] = nodes
        return users_followers[username]

    def get_users_followers(self, users, limit=100, count=300):
        threads = [
            ThreadResult(target=self.get_followers,
                         args=(username,),
                         kwargs={'limit': limit, 'count': count})
            for username in users
        ]
        return [thread.execute() for thread in threads]

    def get_follows(self, username, count=-1, limit=100):
        if self.force_requests or username not in users_follows:
            data = {
                'account': Account(username)
            }
            nodes = self.repeat_load('get_follows', count, limit=limit, data=data)
            if nodes:
                for node in nodes:
                    obj_media[node.username] = node
            users_follows[username] = nodes
        return users_follows[username]

    def get_users_follows(self, users, limit=100, count=300):
        threads = [
            ThreadResult(target=self.get_follows,
                         args=(username,),
                         kwargs={'limit': limit, 'count': count})
            for username in users
        ]
        return [thread.execute() for thread in threads]

    def get_media(self, obj):
        if self.force_requests or str(obj) not in obj_media:
            response = self.make_request('get_media', obj)
            if response is ACCOUNT_DOES_NOT_EXIST:
                obj_media[str(obj)] = None
            else:
                obj_media[str(obj)] = obj
        return obj_media[str(obj)]

    def get_objects_medias(self, objects):
        threads = [
            ThreadResult(target=self.get_media, args=(obj,))
            for obj in objects
        ]
        return [thread.execute() for thread in threads]

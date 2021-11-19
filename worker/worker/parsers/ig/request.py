import logging
import random
import time

from worker.helpers.tools import sequential_start
from worker.parsers.ig.agent import InstAgent
from worker.parsers.ig.state import *


logger = logging.getLogger()


class InstRequest:
    force_requests = False
    good_agents = set()
    wait_agents = set()
    active_agents = set()
    used_agents = set()
    last_agent_review_time = 0

    @classmethod
    def print_stat(cls):
        logger.debug('Good agents count:', len(cls.good_agents))
        logger.debug('Wait agents count:', len(cls.wait_agents))
        logger.debug('Active agents count:', len(cls.active_agents))
        logger.debug('Used agents count:', len(cls.used_agents))
        logger.debug('Last_agent_review_time:', time.time() - cls.last_agent_review_time)
        logger.debug('Force requests:', cls.force_requests)

    @classmethod
    @sequential_start
    def review_wait_agents(cls):
        if time.time() - cls.last_agent_review_time < 20:
            return

        to_good = set()
        to_dead = set()
        for agent in cls.wait_agents:
            if agent._status() == STATUS_GOOD_AGENT:
                to_good.add(agent)
            if agent._status() == STATUS_DEAD_AGENT:
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
        agent_status = agent._status()
        if agent_status == STATUS_DEAD_AGENT:
            with open('data/dead_agents', 'a') as file:
                file.write(agent.username + ',')
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

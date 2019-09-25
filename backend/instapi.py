import time
from instagram import Account, Media, WebAgent, WebAgentAccount
from instagram.exceptions import HTTPError
from queue import Queue
from threading import Thread
from app_data import inst_accounts_data

inst_agents = {}
agents_queue = Queue()


class InstRequest:
    def get_agent(self):
        if agents_queue.empty():
            agent = self.create_agent()
            if agent:
                agents_queue.put((agent, time.time() - 10))
            else:
                print('EMPTY AGENTS LIST')
                time.sleep(1)
                return self.get_agent()

        agent, last_call_time = agents_queue.get()
        if time.time() - last_call_time < 2:
            new_agent = self.create_agent()
            if new_agent:
                agents_queue.put((new_agent, time.time() - 10))
            else:
                print('NEED MORE INST AGENTS!')

            wait_time = max(0, 2 - (time.time() - last_call_time))
            print('SLEEP {} seconds'.format(wait_time))
            time.sleep(wait_time)
        return agent, last_call_time

    @staticmethod
    def return_agent(agent):
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
            if username not in inst_agents:
                print('### Add inst agent: {}'.format(username))
                new_agent = WebAgentAccount(username)
                new_agent.auth(password)
                inst_agents[username] = new_agent
                return new_agent

        return None

    def make_request(self, func_name, **kwargs):
        agent, last_call_time = self.get_agent()
        try:
            print('* Inst api call: {}, agent: {}'.format(func_name, agent.username))
            result = getattr(agent, func_name)(**kwargs)
            self.return_agent(agent)
            return result
        except HTTPError:
            self.return_agent(agent)
            raise Exception('[429] inst error')


class InstAPI(InstRequest):
    def repeat_load(self, func_name, count, limit, data=None):
        data['count'] = limit
        if count < -1 or count == 0:
            raise ValueError('Wrong count value')
        items, pointer = self.make_request(func_name, **data)
        count -= limit
        while pointer and (count == -1 or count > 0):
            items_, pointer = self.make_request(func_name,
                                                **data,
                                                pointer=pointer)
            count -= limit
            items += items_

        return items

    def get_followers(self, username, count=-1, limit=100, results=None, result_index=None):
        data = {
            'account': Account(username)
        }
        res = self.repeat_load('get_followers', count, limit=limit, data=data)
        if results:
            results[result_index] = res
        return res

    def get_users_followers(self, users, limit=100, count=300):
        results = [None] * len(users)
        threads = [
            Thread(target=self.get_followers,
                   args=(username,),
                   kwargs={'results': results, 'result_index': i, 'limit': limit, 'count': count})
            for i, username in enumerate(users)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return results

    def get_following(self, username):
        pass

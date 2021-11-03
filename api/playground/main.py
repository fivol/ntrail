from pprint import pprint

from playground.time_tools import print_time
from worker import Engine
from core import VKUser
from server_stand import ServerStand


if __name__ == '__main__':
    with Engine(caching=False):
        with ServerStand(debug=False) as server:
            with print_time():
                pprint(server.run(['user'], user='ffboris'))

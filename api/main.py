from worker import Engine
from core import VKUser
from server_stand import ServerStand


if __name__ == '__main__':
    with Engine(caching=False):
        with ServerStand() as server:
            print(server.run(['basic'], user='ffboris'))

from worker import Engine
import config
from modules import VKUser

my_id = 245089915


def main():
    print(VKUser(245089915))
    print(VKUser(245089915).friends())
    print(VKUser(1))


if __name__ == '__main__':
    with Engine():
        main()

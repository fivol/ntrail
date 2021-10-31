from worker import Engine, VkMethods
# from modules import VKUser

my_id = 245089915


def main():
    print(VkMethods.user.sync(1))


if __name__ == '__main__':
    pass
    with Engine():
        print(VkMethods.user.sync(1))
        print(VkMethods.user.sync(1))

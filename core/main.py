from worker import VkMethods
import asyncio

if __name__ == '__main__':
    print(VkMethods.friends.sync(245089915))
    print(VkMethods.user.sync(245089915))


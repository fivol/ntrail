import asyncio
import logging

from worker import Engine, VkMethods
from worker.parsers.ig.instagramlib import Account, WebAgentAccount

logger = logging.getLogger(__name__)
logger.debug('123')

# exit(0)
#
# from igramscraper.instagram import Instagram
#
# instagram = Instagram()
#
# # authentication supported
# instagram.with_credentials('fiobond', 'dlz08UtKFinst')
# instagram.login()
#
# #Getting an account by id
# account = instagram.get_account_by_id(3)
#
# # Available fields
# print('Account info:')
# print('Id: ', account.identifier)
# print('Username: ', account.username)
# print('Full name: ', account.full_name)
# print('Biography: ', account.biography)
# print('Profile pic url: ', account.get_profile_picture_url())
# print('External Url: ', account.external_url)
# print('Number of published posts: ', account.media_count)
# print('Number of followers: ', account.followed_by_count)
# print('Number of follows: ', account.follows_count)
# print('Is private: ', account.is_private)
# print('Is verified: ', account.is_verified)
#
# # or simply for printing use
# print(account)


async def main():
    async with Engine():
        await VkMethods.friends(245089915)

if __name__ == '__main__':
    asyncio.run(main())

"""
400 queries with caching: 2140 rps
1000: 290
100 new queries (cache misses) - 200 rps (20 tokens) 2500 with cache
1000 users.get queries without caching - 313 rps (20 tokens) with normal limits (3 and 5 rps per token)

10000 users data collected with rps 3797 
25000 with rps 4459. Splitter divided it into 25 users.get queries and execute completes with single query
-> 25000 users in one query
"""

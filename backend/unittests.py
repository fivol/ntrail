import unittest
from tools import *
from vkuser import VKUser
from glbal import logger
import logging
import datetime
from local_cache import LocalCache
from vkcommunity import VKCommunity
from iguser import IGUser
from igcommunity import IGCommunity
from vkgroup import VKGroup
from vkgroup import VKGroups
import warnings
from vkpost import VKPosts
from vkpost import VKPost
from constants import ACCOUNT_STATUS_ABSENT, ACCOUNT_STATUS_PUBLIC


logger.setLevel(logging.WARNING)


# @unittest.skip
class ToolsTest(unittest.TestCase):
    def test_get_obj(self):
        n = 321321
        self.assertEqual(get_obj(n), get_obj(n))
        self.assertIsNone(get_obj(412421412421))

    def test_getset_obj(self):
        keys = [24234214, 'sdflkfdsf', (1, 2)]
        for key in keys:
            set_obj(key, str(key) + '!!!')

        for key in keys:
            self.assertEqual(get_obj(key), str(key) + '!!!')

    def test_get_color(self):
        self.assertEqual(get_color(2), get_color(2))
        self.assertEqual(get_color(5), get_color(5))
        self.assertNotEqual(get_color(1), get_color(3))
        self.assertNotEqual(get_color(0), get_color(5))
        self.assertNotEqual(get_color(10), get_color(9))

    def test_dict_from_dicts(self):
        self.assertRaises(AssertionError, dict_from_dicts, {}, 4)
        self.assertRaises(AssertionError, dict_from_dicts, -3, 4)
        key = 'a'
        dicts = [{'a': 3, 'b': 'x'}, {'a': 24}, {'r': 'lll'}]
        res = {3: {'a': 3, 'b': 'x'}, 24: {'a': 24}}
        self.assertEqual(dict_from_dicts(dicts, key), res)
        self.assertEqual(dict_from_dicts([], 4), {})
        self.assertEqual(dict_from_dicts([{1: 1}, {}, {}], 1),
                         {1: {1: 1}})


class QueriesTest(unittest.TestCase):
    def setUp(self):
        self.begin_time = datetime.datetime.now()
        self.queries_count = LocalCache.count_cached_queries()
        warnings.filterwarnings("ignore")

    def tearDown(self):
        LocalCache.remove_queries_from_time(self.begin_time)
        self.assertEqual(self.queries_count, LocalCache.count_cached_queries())


class VKUserTest(QueriesTest):
    def test_user_init(self):
        self.assertTrue(VKUser('https://vk.com/jolex009').valid)
        self.assertTrue(VKUser('https://vk.com/id119007020').valid)
        self.assertTrue(VKUser('id119007020').valid)
        self.assertTrue(VKUser('jolex009').valid)

        self.assertFalse(VKUser('fdsijafosjaofijidfsj').valid)
        self.assertFalse(VKUser('https://vk.com/id11900702dsfdfdd').valid)
        self.assertFalse(VKUser(49243783724937249732).valid)

        self.assertEqual(VKUser('boris2000n').id, 245089915)

        self.assertEqual(VKUser('jolex009').id, 119007020)
        self.assertEqual(VKUser(119007020).id, 119007020)

        for i in range(5):
            r = random.randint(1000, 10000000)
            self.assertEqual(VKUser(r).status, VKUser(f'id{r}').status)
            self.assertTrue(VKUser.generate_random().valid)

        self.assertRaises(ValueError, VKUser, {1: 2})
        self.assertRaises(TypeError, VKUser, [])
        self.assertEqual(VKUser('').status, ACCOUNT_STATUS_ABSENT)
        self.assertRaises(ValueError, VKUser, -1)
        self.assertIsNone(VKUser('').friends())

    def test_friends(self):
        self.assertGreater(VKUser('jolex009').friends().size, 10)
        self.assertGreater(VKUser.me().friends().size, 10)

    def test_functions(self):
        self.assertEqual(VKUser.get_username('  https://vk.com/jksdaf_ji32 '), 'jksdaf_ji32')
        self.assertEqual(VKUser.me().check_status(), ACCOUNT_STATUS_PUBLIC)
        self.assertIsInstance(VKUser.me().follows(), VKCommunity)
        self.assertIsInstance(VKUser.me().followers(), VKCommunity)


# @unittest.skip
class VKCommunityTest(QueriesTest):

    def test_community_init(self):
        self.assertEqual(VKCommunity().size, 0)
        user1 = VKUser('https://vk.com/anna_bigler')
        user2 = VKUser('jolex009')
        self.assertEqual(VKCommunity([user1, user2]).only_valid().size, 2)
        self.assertEqual(VKCommunity(['anna_bigler', 'jolex009'], clear=True).size, 2)
        VKCommunity([])
        VKCommunity(Counter())
        self.assertRaises(TypeError, VKCommunity, {})
        self.assertRaises(TypeError, VKCommunity, 32)
        users_string = '''
        sfjldsfj https://vk.com/anna_bigler dsfsfa32423478888*
        https://google.com ://
        boris2000n
        https://vk.com/jolex009////
        
        '''
        self.assertEqual(VKCommunity(users_string).size, 2)

    def test_operations(self):
        a = VKCommunity(['anna_bigler', 'jolex009'])
        b = VKUser('jolex009').friends()
        self.assertGreater((a + b).size, a.size)

    def test_generate(self):
        for i in range(5):
            self.assertEqual(VKCommunity.generate_random(20).only_valid().size, 20)


class VKGroupTest(QueriesTest):
    def test_init(self):
        self.assertEqual(VKGroup('https://vk.com/stfivt').valid, True)
        self.assertEqual(VKGroup('https://vk.com/stfivt/').valid, True)
        self.assertEqual(VKGroup('https://vk.com/ovsyanochan').valid, True)
        self.assertEqual(VKGroup('https://vk.com/fsdfkjdlsfjldsfjl/').valid, False)
        self.assertEqual(VKGroup('fds/fdsa/fd/ds/das/dfs/dfs/fffffffijijij').valid, False)
        self.assertEqual(VKGroup(48392472736478).valid, False)
        self.assertEqual(VKGroup(242142131).valid, False)
        self.assertEqual(VKGroup(144624886).valid, True)
        self.assertEqual(VKGroup(45698612).valid, True)
        self.assertRaises(TypeError, VKGroup, ([1, 2, 3],))
        self.assertRaises(TypeError, VKGroup, ({1: 2, 3: 4},))


class VKPostsTest(QueriesTest):
    def test_init(self):
        pass

    def test_get_wall(self):
        self.assertIsInstance(VKUser('https://vk.com/id493754172').posts(), VKPosts)
        self.assertIsNone(VKUser('fdasjlfsdajoifdsfds').posts())
        self.assertIsNone(VKUser(324234243324).posts())
        self.assertIsInstance(VKUser('boris2000n').posts(), VKPosts)
        self.assertEqual(VKUser('boris2000n').posts().size, 0)
        self.assertGreater(VKUser('https://vk.com/id91888646').posts().size, 7)


if __name__ == '__main__':
    unittest.main()

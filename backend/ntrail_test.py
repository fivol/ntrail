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
from vkgroups import VKGroups
logger.setLevel(logging.WARNING)


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


class VKUserTest(unittest.TestCase):
    def setUp(self):
        self.begin_time = datetime.datetime.now()
        self.queries_count = LocalCache.count_cached_queries()

    def tearDown(self):
        LocalCache.remove_queries_from_time(self.begin_time)
        self.assertEqual(self.queries_count, LocalCache.count_cached_queries())

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

        self.assertRaises(TypeError, VKUser, {1: 2})
        self.assertRaises(TypeError, VKUser, [])


if __name__ == '__main__':
    unittest.main()

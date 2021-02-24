from pprint import pprint

from module_vk.vkuser import VKUser
import warnings

# print(VKUser("https://vk.com/id269339915").friends().short_data)
# print(VKUser("https://vk.com/id269339915").friends().process_data())

warnings.filterwarnings("ignore")

# pprint(get_field_values(VKUser.me().groups().data_list(), 'country', key='title'))
# g = VKUser('alice.shtein').groups()
#
# print(len(g.represent()['clusters']['items'][0]['entities']['items']))
# pprint(len(g.get_items()))
# pprint(VKGroups([VKGroup('https://vk.com/fitnessyammy').id]).data_list(full=False))
# VKUser('https://vk.com/id341467094').groups()
# print(VKGroups(VKAPI.get_user_groups(VKUser('https://vk.com/id341467094').id)).full_data[4/]['name'])
(VKUser('boris2000n').friends().clusters().represent())


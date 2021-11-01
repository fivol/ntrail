import warnings
import core.config # noqa
warnings.simplefilter('ignore')
from core.modules import VKUser
from worker import Engine, VkMethods

my_id = 245089915


def main():
    # print(VKUser.extract_username('https://vk.com/ffboris'))
    user = VKUser('ffboris')
    print(user.friends().friends())
    # print(user.data())
    # print(me.photos().data())
    # user.friends().friends().export('csv')
    # print(VkMethods.users.sync([4215845, 4262614, 4583286]))
    # print(VKUser(245089915).friends())
    # print(VKUser(1))


if __name__ == '__main__':
    with Engine(caching=False):
        main()

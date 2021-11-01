import warnings
import core.config # noqa
warnings.simplefilter('ignore')
from core.modules import VKUser
from worker import Engine, VkMethods

my_id = 245089915

# private profiles
# 431956287
# 444845865
# 455899120
# 457559807
# 460844711
# 537901892
# 558287310
# 608492386


def main():

    user = VKUser('https://vk.com/id93454638')
    user.friends().friends().export(filename='.data/dania-freinds-friends.csv')
    user.friends().export(filename='.data/dania-freinds.csv')


if __name__ == '__main__':
    with Engine(caching=True, timeout=10):
        main()

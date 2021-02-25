import re
from ntmodule.selective_query_exeptions import QueryDataException
from module_vk.vkcommunity import VKCommunity
from apimodule_vk.vkapi import VKAPI
from module_vk.vkgroup import VKGroup
from module_vk.vkuser import VKUser
from glbal import logger


class QueryParser:
    available_attributes = ['']

    def __init__(self, query):
        logger.debug("query: %s", query)
        self.query = query

    @staticmethod
    def vk_represent(username):
        vk_resolved = VKAPI.resolve_screen_name(username)
        logger.debug("%s", vk_resolved)

        try:
            t = vk_resolved['type']
            if t == 'user':
                target_class = VKUser
            elif t == 'group' or t == 'page':
                target_class = VKGroup
            else:
                logger.error('Unknown vk id type %s: %s', t, username)
                raise QueryDataException(
                    f'Тип ВК объекта "{t}" пока не поддерживается (введите пользователя или группу)')

            # TODO Тут должно быть еще много типов: музыка, посты, истории
        except KeyError:
            raise QueryDataException('Не удалось распознать ВК id (человек / группа / другое) - скорее всего такого '
                                     'не существует, проверьте написание')

        return target_class(username).represent()

    def represent(self):
        query = self.query
        username_symbols = r'[0-9a-zA-Z.\-_]+'
        vk_username_match = re.search(F'vk.com/({username_symbols})', query)
        full_username_match = re.match(username_symbols, query)
        if vk_username_match:
            username = vk_username_match.group(1)
            logger.debug('VK username match %s', username)
            return self.vk_represent(username)

        elif full_username_match:
            username = full_username_match.group(0)
            logger.debug('Full username match %s', username)
            return self.vk_represent(username)

        else:
            return VKCommunity.search_query(query).represent()

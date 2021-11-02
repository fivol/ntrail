# from server.plugin import BasePlugin
#
#
# class VKConnectionsPlugin(BasePlugin):
#     name = 'connections'
#
#
#
# import datetime
# from contextlib import suppress
# from fastapi import Query, HTTPException
# from starlette import status
#
# from core.modules import VKUser
# from server.routes.auth import check_token
# from server.routes.vk.types import PropertySource, VkUserResponse
# from server.types import ResponseVerbose
#
#
# @app.get('/vk/user/', response_model=VkUserResponse, name='ВК аккаунт')
# async def vk_api() -> dict:
#     """Получить информацию об одном аккаунте ВКонтакте. Запрос собирается на основе списка `options` из аргументов
#     Возможны следующие варианты
#     - basic: только данные самого аккаунта, самые быстрый запрос, возвращает следующую информацию
#     - connections: проанализировать друзей, подписки и подписчиков
#     - groups: добавить поля, связанные с группами, сообществами пользователя
#     """
#     await check_token(token)
#
#     if not options:
#         options.append(VkRequestOption.basic)
#     options = set(options)
#
#     # Данные, которые возвращает запрос
#     user_data = {}
#     user = VKUser(user)
#     if not user.valid:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
#
#     def add_property(key: str, value, confidence: float = None, source: PropertySource = None):
#         """Добавить значение к ответу"""
#         if value is None or value == '':
#             return
#         if verbose == ResponseVerbose.simple:
#             user_data[key] = value
#         elif verbose == ResponseVerbose.normal:
#             property_dict = {
#                 'value': value
#             }
#             if source:
#                 property_dict['source'] = source.name
#             if confidence is not None:
#                 property_dict['confidence'] = min(1.0, max(0.0, confidence))
#             user_data[key] = property_dict
#         else:
#             raise ValueError
#
#     if VkRequestOption.basic in options:
#         add_property('id', user.id, source=PropertySource.page)
#         add_property('url', user.url, source=PropertySource.page)
#         add_property('name', user.name, source=PropertySource.page)
#         add_property('username', user.get_attribute('screen_name'), source=PropertySource.page)
#         add_property('deactivated', user.get_attribute('deactivated'), source=PropertySource.page)
#         add_property('sex', ['not specified', 'female', 'male'][user.get_attribute('sex', 0)],
#                      source=PropertySource.page)
#         bdate = user.get_attribute('bdate')
#         add_property('birth', bdate, source=PropertySource.page)
#         add_property('photo', user.get_attribute('photo_200'), source=PropertySource.page)
#         # Возраст, взятый напрямую со страницы
#         if bdate and len(bdate.split('.')) == 3:
#             age = datetime.datetime.now() - datetime.datetime.strptime(bdate, '%d.%m.%Y')
#             add_property('age', age.days // 365)
#         with suppress(Exception):
#             platform = user.get_attribute('last_seen')['platform']
#             add_property('platform.type', [None, 'web', 'apple', 'apple', 'android', 'web', 'web', 'web'][platform],
#                          source=PropertySource.page)
#         add_property('followers.count', user.get_attribute('followers_count'), source=PropertySource.page)
#         with suppress(Exception):
#             add_property('subscriptions.count', user.get_attribute('counters')['subscriptions'],
#                          source=PropertySource.page)
#             add_property('followers.count', user.get_attribute('counters')['followers'], source=PropertySource.page)
#         with suppress(Exception):
#             add_property('occupation', user.get_attribute('occupation')['type'], source=PropertySource.page)
#         with suppress(Exception):
#             add_property('university', user.get_attribute('universities')[0]['name'], source=PropertySource.page)
#         with suppress(Exception):
#             add_property('school', user.get_attribute('schools')[0]['name'], source=PropertySource.page)
#
#         with suppress(Exception):
#             add_property('active_user',
#                          datetime.datetime.now() - datetime.datetime.fromtimestamp(
#                              user.get_attribute('last_seen')['time']) < datetime.timedelta(days=3),
#                          source=PropertySource.page)
#         add_property('relation',
#                      [None, 'single', 'in a relationship', 'engaged', 'married', "it's complicated",
#                       'actively searching', 'in love'][user.get_attribute('relation')])
#         with suppress(Exception):
#             add_property('personal',
#                          [None, 'Communist', 'Socialist', 'Moderate', 'Liberal', "Conservative",
#                           'Monarchist', 'Ultraconservative', 'Apathetic', 'Libertian'][
#                              user.get_attribute('personal')['political']])
#         if user.get_attribute("instagram"):
#             add_property('links.instagram', f'https://www.instagram.com/{user.get_attribute("instagram")}/')
#
#     if VkRequestOption.connections in options:
#         from core.modules.vk.vkcommunity import VKCommunity
#         friends: VKCommunity = user.friends()
#         friends_data = friends.process_data()
#
#         def extract_first(key):
#             return {
#                 'key': key,
#                 'value': friends_data[key]['source_list'][0][0].value,
#                 'confidence': round(len(friends_data[key]['source_list'][0][0].id) / len(friends), 2)
#             }
#
#         add_property('friends.count', len(friends), source=PropertySource.friends)
#         with suppress(Exception):
#             if friends_data['age']['count'].value > 4:
#                 add_property('age', friends_data['age']['commonMedian'], source=PropertySource.friends,
#                              confidence=friends_data['age']['count'].value / 100)
#         with suppress(Exception):
#             add_property(**extract_first('city'))
#         with suppress(Exception):
#             add_property(**extract_first('country'))
#         with suppress(Exception):
#             if not len(user.get_attribute('schools', [])):
#                 add_property(**extract_first('school'))
#         with suppress(Exception):
#             if not len(user.get_attribute('universities', [])):
#                 add_property(**extract_first('university'))
#         clusters = friends.pools()
#         add_property('social.groups.all.count', len([cluster for cluster in clusters if len(cluster) > 3]))
#         add_property('social.groups.big.count', len([cluster for cluster in clusters if len(cluster) > 8]))
#         add_property('social.groups.small.count', len([cluster for cluster in clusters if 1 < len(cluster) <= 8]))
#         add_property('social.groups.free.count', len([cluster for cluster in clusters if len(cluster) == 1]))
#
#     if VkRequestOption.groups in options:
#         groups = user.groups()
#         add_property('groups.count', len(groups))
#         groups_data = groups.process_data()
#         add_property('groups.themes', [item[0].value for item in groups_data['activity_pages']['source_list']])
#         add_property('groups.tags', [item[0].value for item in groups_data['name']['source_list']])
#
#     return {
#         'user': user_data
#     }
#

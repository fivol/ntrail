# Список полей ответа API запроса, содержащего информацию о сообществах
groups_full_fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                      'main_section', 'members_count', 'place',
                      'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                      'description', 'site', 'start_date']

# Аналогично для людей. Список полей API запроса
users_full_fields = [
    'photo_200', 'photo_max', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
    'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
    'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
    'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
    'universities', 'verified', 'counters', 'screen_name', 'lists', 'is_closed',
]

group_fields = ['activity', 'age_limits', 'city', 'country', 'has_photo',
                'main_section', 'members_count', 'place',
                'trending', 'verified', 'wall', 'links', 'contacts', 'counters',
                'description', 'site', 'start_date']
groups_fields_string = ','.join(group_fields)
user_fields = ['photo_200', 'about', 'activities', 'bdate', 'books', 'career', 'city', 'connections',
               'sex', 'contacts', 'country', 'education', 'exports', 'followers_count', 'home_town', 'interests',
               'last_seen', 'maiden_name', 'military', 'movies', 'music', 'nickname', 'occupation', 'online',
               'personal', 'quotes', 'relatives', 'relation', 'schools', 'site', 'status', 'trending', 'tv',
               'universities', 'verified', 'counters', 'screen_name', 'lists', 'is_closed', ]

users_fields_string = ','.join(user_fields)
service_token_methods = {'friends', 'resolve', 'friends', 'user_short', 'group_short', 'wall', 'posts', 'albums_ids',
                         'apps'}

user_token_methods = {'groups', 'search', 'members',
                      'user_full', 'group_full', 'photos_ids'}

methods_group_key = {'user_short', 'user_full', 'group_short', 'group_full', 'posts', 'photos_ids', 'albums_ids',
                     'apps'}

available_execute = {'friends', 'groups', 'resolve', 'members'}


VK_API_UNKNOWN_ERROR = 1
UNKNOWN_ERROR = -1
REQUEST_EXECUTE_ERROR = 0
ACCESS_DENIED_ERROR = 15
PRIVATE_PROFILE_ERROR = 30
INVALID_ID_ERROR = 113
ALBUM_ACCESS_DENIED_ERROR = 200
USER_AUTHORIZATION_ERROR = 5

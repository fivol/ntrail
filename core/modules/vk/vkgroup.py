from constants import GROUP_STATUS_ABSENT, GROUP_STATUS_VALID, GROUP_STATUS_DEACTIVATED
from core.module.one_object_represent import OneObjectRepresent
from core.module.tools import once_property, valid_object_method, cache_method
from glbal import logger
from core.modules.vk.vkapi import VKAPI
from core.call_worker.api_errors import APIError, INVALID_ID_ERROR


class VKGroup(OneObjectRepresent):
    id_prefix = 'vkg_'

    def __init__(self, group, **kwargs):
        super().__init__()

        self.id = None
        self.status = None
        if isinstance(group, str):
            groupname = group.strip('/').split('/')[-1]
            user_dict = VKAPI.resolve_screen_name(groupname)
            if not isinstance(user_dict, dict):
                logger.info('VKGroup username does not exist "%s"', groupname)
                self.status = GROUP_STATUS_ABSENT
            elif not user_dict['type'] == 'group':
                logger.info('VKGroup username type is "%s"', user_dict['type'])
                self.status = GROUP_STATUS_ABSENT
            else:
                self.status = GROUP_STATUS_VALID
                self.id = user_dict['object_id']
        elif isinstance(group, int):
            self.id = int(group)
        elif isinstance(group, dict):
            self.id = group['id']
            # self.full_data_ = group
            self.short_data_ = group
        else:
            raise TypeError('VKGroup wrong type', type(group))

    @once_property
    @valid_object_method
    def full_data(self):
        return self.data()
        # TODO Здесь стоит заглушка. Вместо полной подгружается краткая инфа о группах
        # Чтобы вернуть все как было нужно указать full=True
        return VKAPI.get_group_data(self.id, full=False)

    @cache_method
    def data(self, force=False):
        return VKAPI.get_group_data(self.id, full=False, force=force)

    @once_property
    def short_data(self):
        return self.data()
        return VKAPI.get_group_data(self.id, full=False)

    @valid_object_method
    def get_members(self, count=1000):
        from module_vk.vkcommunity import VKCommunity
        if count == -1:
            count = 30000
        members = VKAPI.get_group_members(self.id, count=count)
        return VKCommunity(members)

    @property
    def name(self):
        if not self.valid:
            return 'Не валиден'
        return self.short_data['name']

    def posts(self):
        return VKAPI.get_group_posts(self.id)

    def check_status(self):
        if not self.status:
            user_data = self.short_data
            if APIError.is_error(user_data):
                if user_data.code == INVALID_ID_ERROR:
                    self.status = GROUP_STATUS_ABSENT
                else:
                    raise ValueError('VKGroup short data have unknown value:', user_data)
            else:
                assert isinstance(user_data, dict)
                if 'deactivated' in user_data:
                    self.status = GROUP_STATUS_DEACTIVATED
                else:
                    self.status = GROUP_STATUS_VALID
        return self.status

    @once_property
    def valid(self):
        status = self.check_status()
        assert not (status is None), status
        return status == GROUP_STATUS_VALID

    def get_entities(self):
        return [self.get_entity()]

    def get_params(self, parent=None):
        return {
            'baseType': 'groups',
            'service': 'vk',
            'type': 'group',
            'fullEntitiesCount': 1,
            'id': self.hash,
            'name': self.name,
            'query': f'GET vk.group {self.full_data["screen_name"]}' if self.valid else ''
        }

    def get_entity(self):
        response = {
            'id': self.get_id(),
            'accessStatus': self.check_status(),
        }
        if not self.valid:
            return {
                **response,
                'url': self.url,
                'img': 'https://vk.com/images/deactivated_100.png?ava=1',
                'name': 'Группа не валидена',
                'valid': False,
                'properties': {
                    'weight': 0,
                    'connections': [],
                }
            }
        return {
            **response,
            'url': self.url,
            'img': self.full_data.get('photo_100', 'https://vk.com/images/camera_100.png?ava=1'),
            'name': self.name,
            'username': self.full_data.get("screen_name", 'id' + str(self.id)),
            'nativeID': self.id,
            'valid': True,
            'verified': self.full_data.get('verified', False),
            'accessStatus': self.check_status(),
            'properties': {
                'weight': 1,
                'connections': []
            }
        }

    @property
    @valid_object_method
    def url(self):
        return f"https://vk.com/{self.short_data['screen_name']}"

from enum import Enum


class AccountStatus(Enum):
    PRIVATE = 'PRIVATE'
    DELETED = 'DELETED'
    BANNED = 'BANNED'
    ABSENT = 'ABSENT'
    PUBLIC = 'PUBLIC'
    VALID = 'VALID'


class GroupStatus(Enum):
    ABSENT = 'ABSENT'
    VALID = 'VALID'
    DEACTIVATED = 'DEACTIVATED'


class CacheType(Enum):
    ONLY_WRITE = 1
    ONLY_READ = 2
    FULL_USE = 3
    IGNORE = 4


NO_AVA_IMG = 'https://vk.com/images/camera_100.png?ava=1'

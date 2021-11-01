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


class PlotType(Enum):
    LINE = 'line'
    CIRCULAR = 'circular'
    HIST = 'hist'

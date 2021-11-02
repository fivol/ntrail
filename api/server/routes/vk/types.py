from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel


class VkUserResponse(BaseModel):
    user: Optional[dict]


class PropertySource(Enum):
    page = auto()
    friends = auto()
    followers = auto()
    following = auto()

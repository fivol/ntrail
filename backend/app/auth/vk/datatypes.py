from dataclasses import dataclass
from pydantic import BaseModel


class VKAccessToken(BaseModel):
    # https://vk.com/dev/authcode_flow_user
    access_token: str
    expires_in: int
    user_id: int

import uuid

from app.db import DBUser
from app.auth.vk.db import VKAuthDB
from functools import lru_cache


class AuthDB:
    """Общие метода для работы с авторизацией"""

    @classmethod
    def create_user(cls) -> DBUser:
        """Creates new NTrail user"""
        return DBUser.create(
            token=uuid.uuid4().hex
        )

    @classmethod
    def get_user(cls, token: str) -> DBUser:
        """Returns db user by token"""
        return DBUser.query.filter(DBUser.token == token).first()

    @classmethod
    def delete_user(cls, user_id: int):
        return DBUser.query.filter(DBUser.id == user_id).delete()

    @classmethod
    def set_dependencies(cls, user: DBUser, original_user_id: int):
        user.depends_on = original_user_id
        user.save()

    @classmethod
    def get_user_by_id(cls, user_id: int):
        return DBUser.find(user_id)

    @classmethod
    @lru_cache(maxsize=10)
    def get_api_token(cls, user_id: int, service: str):
        # TODO заменить str на enum
        if service == 'vk':
            return VKAuthDB.get_access_token(user_id)
        else:
            raise NotImplementedError

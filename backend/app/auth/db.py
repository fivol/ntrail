import uuid

from app.db import DBUser


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

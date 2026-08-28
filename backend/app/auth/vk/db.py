from sqlalchemy.exc import IntegrityError

from auth.vk.datatypes import VKAccessToken
from db import *
from exceptions import DBException
import typing as t


class VKAuthDB:
    """Класс содержит методы для работы с базой данных, используемые при авторизации через ВК"""

    @classmethod
    def auth_vk(cls, user_id: int, token: VKAccessToken, **kwargs):
        """Создается запись авторизации вк пользователя + запись DBUser"""
        # То есть пользователь не отслеживается
        try:
            return DBAuthorization.create(
                local_id=token.user_id,
                token=token.access_token,
                expires_in=token.expires_in,
                service='vk',
                user_id=user_id
            )
        except IntegrityError:
            raise DBException

    @classmethod
    def check_auth(cls, user_id: int) -> bool:
        # TODO надо бы проверять expires_in
        vk_auth_count = DBAuthorization.query.filter(
            DBAuthorization.user_id == user_id,
            DBAuthorization.service == 'vk').count()
        return vk_auth_count > 0

    @classmethod
    def get_user(cls, token: VKAccessToken) -> t.Optional[DBUser]:
        auth_model: DBAuthorization = DBAuthorization.query.filter(
            DBAuthorization.local_id == token.user_id
        ).first()
        if not auth_model:
            return None
        return auth_model.user

    @classmethod
    def get_access_token(cls, user_id: int) -> t.Optional[str]:
        row = DBAuthorization.query.filter(
            DBAuthorization.user_id == user_id,
            DBAuthorization.service == 'vk').first()
        return row and row.token

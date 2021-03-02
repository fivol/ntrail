"""
Тут объявлены модели для базы данных
Отличие от файла models.py в том, что
это важные данные, они сохраняются на сервере баз данных.
Тут хранятся конфиденциальные данные пользователей,
которые нельзя удалять при переезде на другую машину.
Хорошо бы еще и делать резервную копию всех токенов
Они нужны для обращения к API сервисов от имени пользователей
"""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_mixins import ActiveRecordMixin, ReprMixin, TimestampsMixin

Base = declarative_base()


class BaseModel(Base, ActiveRecordMixin, ReprMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
    pass


class DBUser(BaseModel, TimestampsMixin):
    """Модель представляет собой пользователя сервиса NTrail"""
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    status = Column(String)


class DBAuthorization(BaseModel, TimestampsMixin):
    """Авторизация в каком либо сервисе, однозначно соответствует пользователю
    Предоставляет доступ к API"""
    __tablename__ = 'auth'
    # For example: 'vk', 'instagram', 'telegram'...
    service = Column(String)
    token = Column(String(1024))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User')

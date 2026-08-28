"""
Тут объявлены модели для базы данных
Отличие от файла models.py в том, что
это важные данные, они сохраняются на сервере баз данных.
Тут хранятся конфиденциальные данные пользователей,
которые нельзя удалять при переезде на другую машину.
Хорошо бы еще и делать резервную копию всех токенов
Они нужны для обращения к API сервисов от имени пользователей
"""
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_mixins import ActiveRecordMixin, ReprMixin, TimestampsMixin

from config import MAIN_DB_URL, DEBUG_MODE

Base = declarative_base()


class BaseModel(Base, ActiveRecordMixin, ReprMixin, TimestampsMixin):
    """Модели на основе https://github.com/absent1706/sqlalchemy-mixins"""
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
    pass


class DBUser(BaseModel):
    """Модель представляет собой пользователя сервиса NTrail"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    # Перенаправляет на другого пользователя. Нужно для переадресации после авторизации
    # При первой возможности перезаписывается на токен оригинала. То есть на модель,
    # на которую ссылается depends_on
    depends_on = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    # refers to depends_on
    token = Column(String)
    username = Column(String, nullable=True)
    status = Column(String, nullable=True)
    auths = relationship('DBAuthorization')


class DBAuthorization(BaseModel):
    """Авторизация в каком либо сервисе, однозначно соответствует пользователю
    Предоставляет доступ к API"""
    __tablename__ = 'auth'
    # For example: 'vk', 'instagram', 'telegram'...
    id = Column(Integer, primary_key=True)
    service = Column(String)
    local_id = Column(Integer)
    token = Column(String(1024))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    expires_in = Column(Integer)
    user = relationship('DBUser')

    # Уникальная пара сервиса и id пользователя в этом сервисе, например
    # (service: vk, local_id: 21432312) - user_id в вк
    # Возможно придется удалить это ограничение при не отсутствии
    # доступа к local_id какого-либо ресурса (пока с вк все норм)
    __table_args__ = (
        UniqueConstraint(
            service,
            local_id),
    )


engine = create_engine(MAIN_DB_URL, echo=False)
# # autocommit=True - it's to make you see data in 3rd party DB view tool
#
if DEBUG_MODE:
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

session = scoped_session(sessionmaker(bind=engine, autocommit=True))
#
# # setup base model: inject session so it can be accessed from model
BaseModel.set_session(session)

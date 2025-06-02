from typing import Callable

from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from src.parcel_service.core.container import AppContainer
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.infrastructure.unitofwork.uow import UnitOfWork

def build_session_cash_key(session_id: str = "*") -> str:
    """
    Формирует ключ для кеша на основе session_id.

    :param session_id: Идентификатор сессии. По умолчанию "*".
    :type session_id: str
    :return: Строка с ключом кеша.
    :rtype: str
    """
    return f"x-session-id:{session_id}"

def build_redis_cash_cash_key(*args: str) -> str:
    """
    Формирует уникальный ключ для кеша Redis на основе переданных аргументов.

    Каждый аргумент добавляется в ключ через двоеточие.

    Пример:
        build_redis_cash_cash_key("parcel", "session123", "parcel456")
        → "cache:parcel:session123:parcel456"

    :param args: Произвольное количество строк, составляющих части ключа.
    :type args: str
    :return: Собранный ключ в формате "cache:arg1:arg2:...".
    :rtype: str
    """
    return "cache:" + ":".join(str(arg) for arg in args)


def get_session_factory() -> Callable[[], AsyncSession]:
    """
    Получает фабрику сессий SQLAlchemy.

    :return: Функция, возвращающая асинхронную сессию SQLAlchemy.
    :rtype: Callable[[], AsyncSession]
    """
    return AppContainer.session_factory()


def get_redis_session() -> Redis:
    """
    Получает экземпляр Redis для хранения сессий.

    :return: Асинхронный клиент Redis.
    :rtype: Redis
    """
    return AppContainer.redis_session()


def get_redis_cash() -> Redis:
    """
    Получает экземпляр Redis для кеширования данных.

    :return: Асинхронный клиент Redis для кеша.
    :rtype: Redis
    """
    return AppContainer.redis_cash()


def get_mongo_db() -> AsyncIOMotorDatabase:
    """
    Получает экземпляр MongoDB клиента.

    :return: Асинхронный клиент MongoDB.
    :rtype: AsyncIOMotorDatabase
    """
    return AppContainer.mongo_db()


def get_uow() -> IUnitOfWork:
    """
    Получает экземпляр Unit of Work для работы с транзакциями и репозиториями.

    :return: Экземпляр Unit of Work.
    :rtype: IUnitOfWork
    """
    session_factory = AppContainer.session_factory()
    repo_factory = AppContainer.repo_factory()
    return UnitOfWork(session_factory=session_factory, repository_factory=repo_factory)


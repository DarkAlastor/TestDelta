from typing import Callable

import redis.asyncio as redis
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.parcel_service.core.config import Settings
from src.parcel_service.domain.interfaces.repository import IRepositoryFactory
from src.parcel_service.infrastructure.db.redis.redis import create_redis_pool
from src.parcel_service.infrastructure.db.sql.engine import create_db_engine, create_session_factory
from src.parcel_service.infrastructure.repository.factory import RepositoryFactory
from src.parcel_service.infrastructure.repository.registry import RepositoryRegistry


class AppContainer:
    """
    Контейнер приложения, инициализирующий и предоставляющий доступ к общим зависимостям.

    Используется для хранения и извлечения общих компонентов, таких как:
    - SQLAlchemy engine и session factory
    - MongoDB клиент
    - Redis клиенты
    - Фабрика репозиториев

    Хранит ссылку на FastAPI-приложение через `FastAPI.state`.

    :cvar _app: Экземпляр FastAPI-приложения (инициализируется один раз).
    :vartype _app: Optional[FastAPI]
    """

    _app: FastAPI | None = None

    @classmethod
    def init(cls, app: FastAPI, settings: Settings) -> None:
        """
        Инициализирует контейнер приложения и сохраняет зависимости в состоянии FastAPI.

        :param app: Экземпляр FastAPI-приложения.
        :type app: FastAPI
        :param settings: Настройки приложения.
        :type settings: Settings
        """
        cls._app = app

        # Инициализация MongoDb
        cls._mongo_client = AsyncIOMotorClient(settings.mongo.uri)
        cls._mongo_db = cls._mongo_client[settings.mongo.db_name]

        app.state.app_settings = settings.app
        app.state.db_engine = create_db_engine(db_settings=settings.database, debug=settings.app.debug)
        app.state.async_session_factory = create_session_factory(engine=app.state.db_engine)
        app.state.repo_factory = RepositoryFactory(RepositoryRegistry.get())
        app.state.mongo_db = AsyncIOMotorClient(settings.mongo.uri)[settings.mongo.db_name]
        app.state.redis_session = create_redis_pool(settings.redis, db=0)
        app.state.redis_cash = create_redis_pool(settings.redis, db=1)

    @classmethod
    async def shutdown(cls) -> None:
        """
        Завершает работу приложения: останавливает thread-пулы и закрывает соединения с базой данных.

        :raises RuntimeError: Если контейнер не был инициализирован.
        """
        if cls._app is None:
            raise RuntimeError("App is not initialized")

        if hasattr(cls._app.state, "thread_executor"):
            cls._app.state.thread_executor.shutdown(wait=True)

        if hasattr(cls._app.state, "db_engine"):
            await cls._app.state.db_engine.dispose()

    @classmethod
    def get(cls) -> FastAPI:
        """
         Возвращает текущий экземпляр FastAPI-приложения.

         :raises RuntimeError: Если контейнер не был инициализирован.
         :return: FastAPI-приложение.
         :rtype: FastAPI
         """
        if cls._app is None:
            raise RuntimeError("App is not initialized")
        return cls._app

    @classmethod
    def redis_session(cls) -> redis.Redis:
        """
        Возвращает экземпляр Redis, используемый для хранения сессий.

        :return: Redis клиент.
        :rtype: redis.Redis
        """
        if cls.get().state.redis_session is None:
            raise RuntimeError("Redis session is not initialized")
        return cls.get().state.redis_session

    @classmethod
    def mongo_db(cls) -> AsyncIOMotorDatabase:
        """
        Возвращает экземпляр MongoDB.

        :return: MongoDB клиент.
        :rtype: AsyncIOMotorDatabase
        """
        if cls.get().state.mongo_db is None:
            raise RuntimeError("MongoDB is not initialized")
        return cls.get().state.mongo_db

    @classmethod
    def redis_cash(cls) -> redis.Redis:
        """
        Возвращает экземпляр Redis, используемый для кеширования.

        :return: Redis клиент.
        :rtype: redis.Redis
        """
        if cls.get().state.redis_cash is None:
            raise RuntimeError("Redis cache is not initialized")
        return cls.get().state.redis_cash

    @classmethod
    def repo_factory(cls) -> IRepositoryFactory:
        """
        Возвращает фабрику репозиториев.

        :return: Экземпляр IRepositoryFactory.
        :rtype: IRepositoryFactory
        """
        if cls.get().state.repo_factory is None:
            raise RuntimeError("Repository factory is not initialized")
        return cls.get().state.repo_factory

    @classmethod
    def session_factory(cls) -> Callable[[], AsyncSession]:
        """
        Возвращает фабрику SQLAlchemy-сессий.

        :return: Фабрика сессий.
        :rtype: Callable[[], AsyncSession]
        """
        if cls.get().state.async_session_factory is None:
            raise RuntimeError("Session factory is not initialized")
        return cls.get().state.async_session_factory

def register_container(app: FastAPI, settings:Settings) -> None:
    """
    Регистрирует все зависимости в контейнере приложения.

    :param app: FastAPI-приложение, в которое будет внедрён контейнер.
    :type app: FastAPI
    :param settings: Конфигурация приложения.
    :type settings: Settings
    """
    AppContainer.init(app=app, settings=settings)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.parcel_service.core.config import DatabaseSettings

from .url_resolver import make_database_url


def create_db_engine(db_settings: DatabaseSettings, debug: bool = False) -> AsyncEngine:
    """
    Создаёт асинхронный SQLAlchemy engine на основе переданных настроек.

    :param db_settings: Настройки подключения к базе данных (тип, URL, пул, таймауты и т.д.).
    :type db_settings: DatabaseSettings
    :param debug: Включает SQL-отладку (выводит SQL-запросы в консоль), по умолчанию False.
    :type debug: bool
    :return: Асинхронный SQLAlchemy engine.
    :rtype: AsyncEngine
    """
    db_url = make_database_url(db_settings=db_settings)

    connect_args: dict = {}
    kwargs: dict = {
        "echo": debug,
        "future": True,
    }

    if db_settings.type.startswith("sqlite") or db_settings.type.startswith("inmemory"):
        connect_args = {"check_same_thread": False}
        if db_settings.isolation_level:
            kwargs["isolation_level"] = db_settings.isolation_level
    else:
        kwargs.update({
            "pool_size": db_settings.pool_size,
            "max_overflow": db_settings.max_overflow,
            "pool_timeout": db_settings.pool_timeout,
            "pool_recycle": db_settings.pool_recycle,
            "isolation_level": db_settings.isolation_level,
        })

    return create_async_engine(db_url, connect_args=connect_args, **kwargs)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Создаёт фабрику асинхронных сессий SQLAlchemy.

    :param engine: Асинхронный SQLAlchemy engine.
    :type engine: AsyncEngine
    :return: Фабрика для создания асинхронных сессий.
    :rtype: async_sessionmaker[AsyncSession]
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
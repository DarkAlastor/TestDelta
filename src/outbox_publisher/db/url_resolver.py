from src.outbox_publisher.core.config import DatabaseSettings

def make_database_url(db_settings: DatabaseSettings) -> str:
    """
    Формирует асинхронный URL подключения к базе данных на основе настроек.

    Используется SQLAlchemy с async-драйверами (`asyncpg`, `aiomysql`, `aiosqlite`).

    :param db_settings: Объект с настройками подключения к БД.
    :type db_settings: DatabaseSettings
    :return: Асинхронный URL подключения (например, `postgresql+asyncpg://...`).
    :rtype: str
    """
    db_type = db_settings.type.lower()

    if db_type == "inmemory":
        return "sqlite+aiosqlite:///:memory:"

    if db_type == "sqlite":
        return f"sqlite+aiosqlite:///{db_settings.name}.db"

    driver = {
        "postgres": "asyncpg",
        "postgresql": "asyncpg",
        "mysql": "aiomysql",
    }.get(db_type)

    # Для postgres, mysql и других SQLAlchemy-подобных
    return f"{db_type}+{driver}://{db_settings.user}:{db_settings.password}@{db_settings.host}:{db_settings.port}/{db_settings.name}"
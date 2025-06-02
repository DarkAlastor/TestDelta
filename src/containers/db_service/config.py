from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    """
    Настройки подключения к базе данных.

    :ivar type: Тип базы данных (например, 'postgresql+asyncpg').
    :vartype type: str
    :ivar host: Адрес хоста базы данных.
    :vartype host: str
    :ivar port: Порт подключения.
    :vartype port: int
    :ivar user: Имя пользователя.
    :vartype user: str
    :ivar password: Пароль.
    :vartype password: str
    :ivar name: Название базы данных.
    :vartype name: str
    :ivar pool_size: Размер пула соединений.
    :vartype pool_size: int
    :ivar max_overflow: Максимальное количество дополнительных соединений.
    :vartype max_overflow: int
    :ivar pool_timeout: Время ожидания соединения из пула.
    :vartype pool_timeout: int
    :ivar pool_recycle: Период перераспределения соединений.
    :vartype pool_recycle: int
    :ivar isolation_level: Уровень изоляции транзакций.
    :vartype isolation_level: str
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="DATABASE_")
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "secret"
    name: str = "test_db.sqlite"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    isolation_level: str = "REPEATABLE READ"
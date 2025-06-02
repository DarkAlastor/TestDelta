from pathlib import Path
from typing import Type

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class LoggingSettings(BaseSettings):
    """
    Настройки логирования.

    :ivar enabled: Включено ли логирование.
    :vartype enabled: bool
    :ivar level: Уровень логирования (например, INFO, DEBUG).
    :vartype level: str
    :ivar friendly_asc: Включить ли дружественный ASCII-вывод.
    :vartype friendly_asc: bool
    :ivar backtrace: Включить ли трассировку стека при исключениях.
    :vartype backtrace: bool
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="LOGGING_")
    enabled: bool = True
    level: str = "INFO"
    friendly_asc: bool = False
    backtrace: bool = False

class ConfigMetaFastApi(BaseSettings):
    """
    Мета-информация для FastAPI-приложения (название, версия, документация и др.).

    :ivar title_app: Название приложения.
    :vartype title_app: str
    :ivar version_app: Версия приложения.
    :vartype version_app: str
    :ivar description_app: Описание приложения.
    :vartype description_app: str
    :ivar docs_url_app: URL для Swagger UI.
    :vartype docs_url_app: Optional[str]
    :ivar redoc_url_app: URL для ReDoc.
    :vartype redoc_url_app: Optional[str]
    :ivar openapi_url_app: URL для OpenAPI схемы.
    :vartype openapi_url_app: Optional[str]
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="META_")
    title_app: str = "Service"
    version_app: str = "1.0.0"
    description_app: str = "Template Service"
    docs_url_app: str| None = None
    redoc_url_app: str| None = None
    openapi_url_app: str| None = None

class AppSettings(BaseSettings):
    """
    Общие настройки приложения.

    :ivar api_version: Версия API (например, 'v1').
    :vartype api_version: str
    :ivar debug: Флаг режима отладки.
    :vartype debug: bool
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="APP_")
    api_version: str = "v1"
    debug: bool = False

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
    type: str
    host: str
    port: int
    user: str
    password: str
    name: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    isolation_level: str = "REPEATABLE READ"

class RedisSettings(BaseSettings):
    """
    Настройки подключения к Redis.

    :ivar url: Полный URL подключения.
    :vartype url: str
    :ivar max_connections: Максимум соединений.
    :vartype max_connections: int
    :ivar decode_responses: Автоматическое декодирование строк.
    :vartype decode_responses: bool
    :ivar socket_timeout: Таймаут сокета.
    :vartype socket_timeout: int
    :ivar retry_on_timeout: Повторить при таймауте.
    :vartype retry_on_timeout: bool
    :ivar health_check_interval: Интервал проверки соединения.
    :vartype health_check_interval: int
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="REDIS_")
    url: str
    max_connections: int = 20
    decode_responses: bool = True
    socket_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30

class MongoDbSettings(BaseSettings):
    """
    Настройки подключения к MongoDB.

    :ivar uri: Mongo URI.
    :vartype uri: str
    :ivar db_name: Название базы данных.
    :vartype db_name: str
    :ivar collection_name: Название коллекции.
    :vartype collection_name: str
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="MONGO_")
    uri: str
    db_name: str
    collection_name: str

class Settings(BaseModel):
    """
    Основной агрегирующий класс настроек приложения.

    :ivar app: Настройки приложения.
    :vartype app: AppSettings
    :ivar meta: Мета-информация для FastAPI.
    :vartype meta: ConfigMetaFastApi
    :ivar logging: Настройки логирования.
    :vartype logging: LoggingSettings
    :ivar database: Настройки базы данных.
    :vartype database: DatabaseSettings
    :ivar redis: Настройки Redis.
    :vartype redis: RedisSettings
    :ivar mongo: Настройки MongoDB.
    :vartype mongo: MongoDbSettings
    """

    app: AppSettings
    meta: ConfigMetaFastApi
    logging: LoggingSettings
    database: DatabaseSettings
    redis: RedisSettings
    mongo: MongoDbSettings

    @classmethod
    def load(cls, env_file: Path = Path(".env")) -> "Settings":
        # Загружаем переменные из .env в os.environ
        from dotenv import load_dotenv
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)

        # Создаём каждую секцию, каждая из них берёт из os.environ
        field_models: dict[str, Type[BaseSettings]] = {
            "app": AppSettings,
            "meta": ConfigMetaFastApi,
            "logging": LoggingSettings,
            "database": DatabaseSettings,
            "mongo": MongoDbSettings,
            "redis": RedisSettings,
        }

        kwargs = {key: model() for key, model in field_models.items()}
        return cls(**kwargs)
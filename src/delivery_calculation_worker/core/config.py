from pathlib import Path
from typing import Type

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class LoggingSettings(BaseSettings):
    """
    Конфигурация логирования.

    :param enabled: Включено ли логирование.
    :param level: Уровень логирования (например, "INFO", "DEBUG").
    :param friendly_asc: Человекочитаемый вывод логов (для dev-среды).
    :param backtrace: Показывать ли подробный backtrace при исключениях.
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="LOGGING_")
    enabled: bool = True
    level: str = "INFO"
    friendly_asc: bool = False
    backtrace: bool = False

class DatabaseSettings(BaseSettings):
    """
    Конфигурация подключения к реляционной базе данных (PostgreSQL и др.).

    :param type: Тип базы данных (например, postgresql).
    :param host: Хост БД.
    :param port: Порт подключения.
    :param user: Имя пользователя.
    :param password: Пароль.
    :param name: Имя базы данных.
    :param pool_size: Размер пула соединений.
    :param max_overflow: Допустимое количество соединений сверх пула.
    :param pool_timeout: Время ожидания соединения из пула.
    :param pool_recycle: Период (в секундах) для повторного использования соединения.
    :param isolation_level: Уровень изоляции транзакций.
    :param echo: Логировать SQL-запросы.
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
    echo: bool = False

class MongoDbSettings(BaseSettings):
    """
    Конфигурация подключения к MongoDB.

    :param uri: URI подключения к Mongo.
    :param db_name: Название базы данных.
    :param collection_name: Название коллекции, по умолчанию используется для логов/событий.
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="MONGO_")
    uri: str
    db_name: str
    collection_name: str

class RedisSettings(BaseSettings):
    """
    Конфигурация подключения к Redis.

    :param url: URI подключения к Redis.
    :param max_connections: Максимальное количество соединений в пуле.
    :param decode_responses: Декодировать ли ответы (в строки).
    :param socket_timeout: Таймаут сокета Redis (в секундах).
    :param retry_on_timeout: Повторять ли запросы при таймауте.
    :param health_check_interval: Интервал проверки соединения.
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="REDIS_")
    url: str
    max_connections: int = 20
    decode_responses: bool = True
    socket_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30

class RabbitMqSettings(BaseSettings):
    """
    Конфигурация подключения к RabbitMQ.

    :param url: URI подключения к RabbitMQ.
    :param routing_key: Routing key для публикации/прослушивания.
    :param exchange: Название exchange.
    :param queue: Название очереди.
    :param prefetch_count: Количество сообщений, обрабатываемых одновременно.
    :param consumer_tag: Уникальный тег консьюмера.
    :param durable: Устойчивость очереди (сохранение после рестарта брокера).
    :param auto_ack: Автоматическое подтверждение сообщений.
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="RABBITMQ_")
    url: str
    routing_key: str
    exchange: str

    queue: str = "parcel_registry_queue"
    prefetch_count: int = 10
    consumer_tag: str = "delivery_worker"
    durable: bool = True
    auto_ack: bool = False



class Settings(BaseModel):
    """
    Главная модель настроек приложения.

    Объединяет все конфигурационные блоки:
    - logging
    - database
    - rabbitmq
    - mongo
    - redis
    """

    logging: LoggingSettings
    database: DatabaseSettings
    rabbitmq: RabbitMqSettings
    mongo: MongoDbSettings
    redis: RedisSettings

    @classmethod
    def load(cls, env_file: Path = Path(".env")) -> "Settings":
        """
        Загружает настройки из .env файла (если он существует) и переменных окружения.

        :param env_file: Путь к .env файлу.
        :return: Экземпляр класса Settings с заполненными конфигурациями.
        """
        # Загружаем переменные из .env в os.environ
        from dotenv import load_dotenv
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)

        # Создаём каждую секцию, каждая из них берёт из os.environ
        field_models: dict[str, Type[BaseSettings]] = {
            "logging": LoggingSettings,
            "database": DatabaseSettings,
            "rabbitmq": RabbitMqSettings,
            "mongo": MongoDbSettings,
            "redis": RedisSettings
        }

        kwargs = {key: model() for key, model in field_models.items()}
        return cls(**kwargs)
from pathlib import Path
from typing import Type

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppPublisher(BaseSettings):
    """
    Настройки публикатора событий из Outbox.

    :param batch_size: Количество событий в одном батче для обработки.
    :param sleep_interval: Интервал ожидания (в секундах) между итерациями.
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="PUBLISHER_")
    batch_size: int = 50
    sleep_interval: int = 5

class LoggingSettings(BaseSettings):
    """
    Настройки логирования.

    :param enabled: Включено ли логирование.
    :param level: Уровень логирования (например, INFO, DEBUG).
    :param friendly_asc: Формат дружелюбный для консоли.
    :param backtrace: Включить ли подробный backtrace.
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="LOGGING_")
    enabled: bool = True
    level: str = "INFO"
    friendly_asc: bool = False
    backtrace: bool = False

class DatabaseSettings(BaseSettings):
    """
    Настройки подключения к базе данных.

    :param type: Тип БД (например, postgresql).
    :param host: Хост базы данных.
    :param port: Порт подключения.
    :param user: Имя пользователя.
    :param password: Пароль.
    :param name: Название базы данных.
    :param pool_size: Размер пула соединений.
    :param max_overflow: Максимальное количество дополнительных соединений.
    :param pool_timeout: Таймаут получения соединения из пула.
    :param pool_recycle: Время жизни соединения в секундах (для повторного использования).
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

class RabbitMqSettings(BaseSettings):
    """
    Настройки подключения к RabbitMQ.

    :param url: Полный URL подключения к брокеру.
    :param routing_key: Ключ маршрутизации по умолчанию.
    :param exchange: Имя exchange для публикации сообщений.
    :param queue: Имя очереди, с которой связаны события.
    """
    model_config = SettingsConfigDict(extra="ignore", env_prefix="RABBITMQ_")
    url: str
    routing_key: str = "parcel_register"
    exchange: str = ""
    queue: str = "parcel_register"

class Settings(BaseModel):
    """
    Комплексная модель настроек всего приложения.
    Загружается из переменных окружения, .env файла и предоставляет типизированный доступ.
    """

    app : AppPublisher
    logging: LoggingSettings
    database: DatabaseSettings
    rabbitmq: RabbitMqSettings

    @classmethod
    def load(cls, env_file: Path = Path(".env")) -> "Settings":
        """
        Загружает настройки из .env файла (если существует) и окружения.

        :param env_file: Путь до .env файла.
        :type env_file: Path
        :return: Инициализированный объект настроек.
        :rtype: Settings
        """
        # Загружаем переменные из .env в os.environ
        from dotenv import load_dotenv
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)

        # Создаём каждую секцию, каждая из них берёт из os.environ
        field_models: dict[str, Type[BaseSettings]] = {
            "app": AppPublisher,
            "logging": LoggingSettings,
            "database": DatabaseSettings,
            "rabbitmq": RabbitMqSettings,
        }

        kwargs = {key: model() for key, model in field_models.items()}
        return cls(**kwargs)
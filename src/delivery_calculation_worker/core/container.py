from redis import Redis
from typing import Callable, ClassVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.delivery_calculation_worker.core.config import Settings
from src.delivery_calculation_worker.db.redis.redis import create_redis_pool
from src.delivery_calculation_worker.messaging.consumer import RabbitMQConsumer
from src.delivery_calculation_worker.strategies.stratagy import STRATEGY_REGISTRY
from src.delivery_calculation_worker.messaging.handle_message import MessageHandler
from src.delivery_calculation_worker.db.sql.engine import create_db_engine, create_session_factory

class AppContainer:
    """
     IoC-контейнер для хранения глобальных зависимостей delivery_calculation_worker-сервиса.

     Содержит ленивую инициализацию:
     - SQLAlchemy-сессии (PostgreSQL)
     - MongoDB клиента
     - Redis клиента
     - RabbitMQ-консьюмера
     - Обработчика сообщений
     """

    _async_session_factory: ClassVar[Optional[Callable[[], AsyncSession]]] = None
    _mongo_client: ClassVar[Optional[AsyncIOMotorClient]] = None
    _mongo_db: ClassVar[Optional[AsyncIOMotorDatabase]] = None
    _rabbitmq_consumer: ClassVar[Optional[RabbitMQConsumer]] = None
    _message_handler: ClassVar[Optional[MessageHandler]] = None
    _redis_cash: ClassVar[Optional[Redis]] = None

    @classmethod
    async def init(cls, settings: Settings) -> None:
        """
        Инициализирует все зависимости приложения на старте.

        :param settings: Конфигурация приложения со всеми секциями (БД, RabbitMQ, Redis, Mongo).
        :type settings: Settings
        :raises RuntimeError: если инициализация какого-либо компонента невозможна.
        """
        # Инициализация БД
        db_engine = create_db_engine(db_settings=settings.database, debug=settings.database.echo)
        cls._async_session_factory = create_session_factory(engine=db_engine)

        # Инициализация MongoDb
        cls._mongo_client = AsyncIOMotorClient(settings.mongo.uri)
        cls._mongo_db = cls._mongo_client[settings.mongo.db_name]

        cls._redis_cash = create_redis_pool(settings.redis, db=1)

        # Создание handler-а сообщений
        cls._message_handler = MessageHandler(
            strategy_registry=STRATEGY_REGISTRY,
            mongo_db=cls._mongo_db,
            redis = cls._redis_cash,
            session_factory=cls._async_session_factory,
        )

        # Инициализация RabbitMQ Consumer и подключение
        consumer = RabbitMQConsumer()
        await consumer.connect(settings.rabbitmq)
        cls._rabbitmq_consumer = consumer



    @classmethod
    def session_factory(cls) -> Callable[[], AsyncSession]:
        """
        Возвращает фабрику асинхронных SQLAlchemy-сессий.

        :raises RuntimeError: если не инициализирована.
        :return: Callable-функция для получения сессии.
        """
        if cls._async_session_factory is None:
            raise RuntimeError("Session factory is not initialized")
        return cls._async_session_factory

    @classmethod
    def mongo_db(cls) -> AsyncIOMotorDatabase:
        """
        Возвращает подключённую MongoDB-базу.

        :raises RuntimeError: если MongoDB клиент не инициализирован.
        :return: Объект базы данных Mongo.
        """
        if cls._mongo_db is None:
            raise RuntimeError("MongoDB client is not initialized")
        return cls._mongo_db

    @classmethod
    def rabbitmq_consumer(cls) -> RabbitMQConsumer:
        """
        Возвращает экземпляр RabbitMQ-консьюмера.

        :raises RuntimeError: если не инициализирован.
        :return: Объект RabbitMQConsumer.
        """
        if cls._rabbitmq_consumer is None:
            raise RuntimeError("RabbitMQConsumer is not initialized")
        return cls._rabbitmq_consumer

    @classmethod
    def message_handler(cls) -> MessageHandler:
        """
        Возвращает обработчик сообщений, зарегистрированный со стратегиями.

        :raises RuntimeError: если не инициализирован.
        :return: Объект MessageHandler.
        """
        if cls._message_handler is None:
            raise RuntimeError("MessageHandler is not initialized")
        return cls._message_handler
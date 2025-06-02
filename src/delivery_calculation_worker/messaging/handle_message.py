import json
from loguru import logger
from redis import Redis
from typing import Callable
from aio_pika import IncomingMessage
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

class MessageHandler:
    """
    Обработчик входящих сообщений из RabbitMQ.

    Выбирает стратегию обработки события по `event_type`,
    создаёт нужную стратегию и вызывает её `handle(...)`.

    Использует:
    - PostgreSQL сессии (через session_factory),
    - MongoDB для логирования или хранения данных,
    - Redis как кеш или временное хранилище.
    """
    def __init__(
        self,
        strategy_registry: dict,
        mongo_db: AsyncIOMotorDatabase,
        redis: Redis,
        session_factory: Callable[[], AsyncSession],
    ):
        """
        Инициализирует обработчик сообщений.

        :param strategy_registry: Словарь стратегий, где ключ — тип события.
        :param mongo_db: Клиент MongoDB.
        :param redis: Клиент Redis.
        :param session_factory: Фабрика асинхронных SQLAlchemy-сессий.
        """
        self._registry = strategy_registry
        self._mongo_db = mongo_db
        self._session_factory = session_factory
        self._redis = redis

    async def __call__(self, message: IncomingMessage):
        """
        Обрабатывает входящее сообщение RabbitMQ.

        :param message: Объект сообщения от aio-pika.
        """
        async with message.process():
            try:
                raw_body = message.body.decode()
                data = json.loads(raw_body)
                event_type = data.get("event_type")

                if not event_type:
                    logger.warning("Received message without 'event_type': {}", raw_body)
                    return

                strategy_cls = self._registry.get(event_type)
                if not strategy_cls:
                    logger.warning("No strategy found for event_type '{}'", event_type)
                    return

                logger.info("Handling message of type '{}'", event_type)

                async with self._session_factory() as session:
                    strategy = strategy_cls(
                        session=session,
                        mongo_db=self._mongo_db,
                        redis=self._redis,
                    )
                    await strategy.handle(data)
                    logger.info("Successfully handled message of type '{}'", event_type)

            except Exception as e:
                logger.error("Failed to handle message: {}", str(e))


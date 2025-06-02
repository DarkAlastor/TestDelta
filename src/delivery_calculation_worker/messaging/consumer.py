import asyncio
from loguru import logger
from aio_pika import connect_robust, RobustChannel, RobustConnection
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustQueue
from typing import Callable, Optional

from src.delivery_calculation_worker.core.config import RabbitMqSettings


class RabbitMQConsumer:
    """
    Консьюмер сообщений из RabbitMQ с использованием aio-pika (robust connection).

    Отвечает за:
    - подключение к очереди;
    - биндинг к exchange;
    - начало потребления сообщений;
    - корректное закрытие соединения.
    """
    def __init__(self):
        """
        Инициализирует объект, без подключения.
        """
        self._connection: Optional[RobustConnection] = None
        self._channel: Optional[RobustChannel] = None
        self._queue: Optional[AbstractRobustQueue] = None

    async def connect(self, settings: RabbitMqSettings, retry_delay: int = 5):
        """
        Подключается к RabbitMQ и настраивает очередь (passive bind).

        :param settings: Настройки подключения к RabbitMQ.
        :param retry_delay: Время ожидания перед повторной попыткой в случае ошибки.
        :raises Exception: При необработанных исключениях подключения.
        """
        while True:
            try:
                logger.info("Connecting to RabbitMQ (Consumer)...")
                self._connection = await connect_robust(settings.url)
                self._channel = await self._connection.channel()
                await self._channel.set_qos(prefetch_count=settings.prefetch_count)

                # Только подключаемся к существующей
                self._queue = await self._channel.declare_queue(
                    settings.queue,
                    passive=True
                )

                if settings.exchange:
                    await self._queue.bind(settings.exchange, routing_key=settings.routing_key)

                logger.info("Connected to RabbitMQ queue '{}'", settings.queue)
                break

            except Exception as e:
                logger.error("Failed to connect to RabbitMQ: {}. Retrying in {} seconds...", str(e), retry_delay)
                await asyncio.sleep(retry_delay)

    async def start_consuming(self, message_handler: Callable[[AbstractIncomingMessage], asyncio.Future]):
        """
        Начинает потребление сообщений из очереди.

        :param message_handler: Callback-функция для обработки сообщений.
        :raises RuntimeError: Если очередь не была инициализирована.
        """
        if not self._queue:
            raise RuntimeError("RabbitMQ connection is not initialized")

        logger.info("Start consuming messages from queue '{}'...", self._queue.name)
        await self._queue.consume(message_handler, no_ack=False)

    async def close(self):
        """
        Закрывает соединение с RabbitMQ.
        """
        if self._connection:
            await self._connection.close()
            logger.info("RabbitMQ consumer connection closed.")

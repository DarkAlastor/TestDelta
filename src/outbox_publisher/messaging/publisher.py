import json
import asyncio
from loguru import logger
from typing import Optional
from aio_pika import connect_robust, Message, RobustConnection, RobustChannel
from aio_pika.abc import AbstractRobustExchange
from aio_pika.exceptions import ChannelNotFoundEntity, AMQPConnectionError

from src.outbox_publisher.core.config import RabbitMqSettings


class RabbitMQPublisher:
    """
    Публикатор сообщений в RabbitMQ с поддержкой надёжного соединения (robust connection).
    """

    def __init__(self):
        """
        Инициализирует объект без подключения. Подключение выполняется через `connect(...)`.
        """
        self._connection: Optional[RobustConnection] = None
        self._channel: Optional[RobustChannel] = None
        self._exchange: Optional[AbstractRobustExchange] = None

    async def connect(self, settings: RabbitMqSettings, retry_delay: int = 5):
        """
        Устанавливает соединение с RabbitMQ и подключается к exchange.

        :param settings: Настройки подключения к RabbitMQ.
        :type settings: RabbitMqSettings
        :param retry_delay: Интервал между попытками повторного подключения.
        :type retry_delay: int
        :raises Exception: При критической ошибке подключения.
        """
        while True:
            try:
                logger.info("Connecting to RabbitMQ...", url=settings.url)
                self._connection = await connect_robust(settings.url)
                self._channel = await self._connection.channel(publisher_confirms=True)

                self._exchange = await self._channel.get_exchange(
                    name=settings.exchange or "",
                    ensure=True  # ← работает как подключение к существующему exchange
                )

                logger.info(
                    "Successfully connected to RabbitMQ exchange",
                    exchange=settings.exchange or "<default>"
                )
                break  # выход из цикла после успешного подключения

            except AMQPConnectionError as e:
                logger.warning(
                    "Connection to RabbitMQ failed, will retry",
                    error=str(e),
                    retry_delay=retry_delay
                )
                await asyncio.sleep(retry_delay)

            except ChannelNotFoundEntity as e:
                logger.error(
                    "Exchange not found on the broker",
                    exchange=settings.exchange,
                    error=str(e)
                )
                await asyncio.sleep(retry_delay)

            except Exception as e:
                logger.exception("Unexpected error while connecting to RabbitMQ")
                raise

    async def publish(self, message_body: dict, routing_key: str):
        """
        Публикует сообщение в RabbitMQ.

        :param message_body: Словарь, который будет сериализован в JSON.
        :type message_body: dict
        :param routing_key: Ключ маршрутизации для отправки сообщения.
        :type routing_key: str
        :raises RuntimeError: Если соединение не установлено.
        :raises ValueError: Если не передан routing_key.
        """
        if not self._exchange:
            logger.error("Attempted to publish without active exchange connection")
            raise RuntimeError("RabbitMQPublisher is not connected")

        if not routing_key:
            logger.error("Routing key must be provided")
            raise ValueError("routing_key must be provided")

        message = Message(
            body=json.dumps(message_body).encode(),
            content_type="application/json",
            delivery_mode=2  # persistent
        )

        await self._exchange.publish(
            message=message,
            routing_key=routing_key
        )
        logger.debug("Published message to RabbitMQ", routing_key=routing_key, message=message_body)

    async def close(self):
        """
        Закрывает соединение с RabbitMQ, если оно было открыто.
        """
        if self._connection:
            await self._connection.close()
            logger.info("RabbitMQ connection closed")
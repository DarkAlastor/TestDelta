import sys
import logging
import asyncio
from pydantic_settings import BaseSettings
from typing import List
from aio_pika import connect_robust, ExchangeType

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


class RabbitSettings(BaseSettings):
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name: str = "parcel_exchange"
    exchange_type: str = "topic"
    queue_name: str = "parcel_registry_queue"
    routing_keys: List[str] = ["registry_parcel"]  # Поддержка нескольких ключей

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


async def wait_for_rabbitmq(url: str, retries: int = 10, delay: int = 3):
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Trying to connect to RabbitMQ ({attempt}/{retries})...")
            conn = await connect_robust(url)
            await conn.close()
            logger.info("RabbitMQ is ready.")
            return
        except Exception as e:
            logger.warning(f"RabbitMQ not ready yet: {e}")
            await asyncio.sleep(delay)
    raise TimeoutError("RabbitMQ is not ready after multiple attempts.")


async def init_rabbitmq(settings: RabbitSettings):
    await wait_for_rabbitmq(settings.rabbitmq_url)

    connection = await connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        settings.exchange_name,
        type=ExchangeType.TOPIC,
        durable=True
    )

    queue = await channel.declare_queue(
        settings.queue_name,
        durable=True
    )

    for key in settings.routing_keys:
        await queue.bind(exchange, routing_key=key)
        logger.info(f"Bound queue to routing key: {key}")

    logger.info(f"Initialized RabbitMQ: exchange={settings.exchange_name}, queue={settings.queue_name}")
    await connection.close()


if __name__ == "__main__":
    try:
        settings = RabbitSettings()
        asyncio.run(init_rabbitmq(settings))
    except Exception as e:
        logger.error(f"RabbitMQ initialization failed: {e}")
        sys.exit(1)



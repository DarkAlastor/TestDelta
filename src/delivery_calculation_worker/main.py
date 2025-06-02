import asyncio
from loguru import logger
from src.delivery_calculation_worker.core.config import Settings
from src.delivery_calculation_worker.core.container import AppContainer


async def main():
    """
    Точка входа для delivery_calculation_worker.

    Выполняет:
    - загрузку конфигурации;
    - инициализацию зависимостей (БД, Redis, MongoDB, RabbitMQ);
    - запуск обработки входящих сообщений через зарегистрированные стратегии.
    """

    logger.info("Loading settings...")
    settings = Settings.load()
    logger.info("Settings loaded.")

    logger.info("Initializing application container...")
    await AppContainer.init(settings)
    logger.info("Dependencies initialized.")

    message_handler = AppContainer.message_handler()

    logger.info("Starting RabbitMQ consumer...")
    await AppContainer.rabbitmq_consumer().start_consuming(message_handler=message_handler)
    logger.info("Application is running and consuming messages.")

    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")

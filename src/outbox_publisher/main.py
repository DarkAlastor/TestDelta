import asyncio
from loguru import logger
from src.outbox_publisher.core.config import Settings
from src.outbox_publisher.core.container import AppContainer
from src.outbox_publisher.worker import run_outbox_loop

async def main():
    """
    Главная точка входа в приложение.

    - Загружает конфигурацию из .env и переменных окружения.
    - Инициализирует зависимости (БД, RabbitMQ).
    - Запускает основной бесконечный цикл обработки Outbox событий.
    """
    logger.info("Loading application settings...")
    settings = Settings.load()
    logger.info("Settings loaded successfully.")

    logger.info("Initializing dependencies...")
    await AppContainer.init(settings)
    logger.info("Dependencies initialized.")

    # Далее запуск основного цикла
    logger.info("Starting outbox event loop...")
    await run_outbox_loop(settings=settings.app)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")

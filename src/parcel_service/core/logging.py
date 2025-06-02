import sys

from loguru import logger

from src.parcel_service.core.config import Settings


def config_logging(settings: Settings):
    logger.remove()

    if not settings.logging.enabled:
        return  # Логирование полностью выключено

    # Устанавливаем значения по умолчанию для extra
    logger.configure()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level> | "
        "request_id={extra[request_id]} client_id={extra[client_id]}"
    )

    # Лог в консоль (stdout)
    logger.add(
        sink=sys.stderr,
        level=settings.logging.level,
        enqueue=settings.logging.friendly_asc,
        format=log_format,
        backtrace=settings.logging.backtrace,
        diagnose=settings.app.debug,
    )
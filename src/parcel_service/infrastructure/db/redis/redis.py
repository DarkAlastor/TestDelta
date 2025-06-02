from urllib.parse import urlparse, urlunparse

import redis.asyncio as redis
from loguru import logger

from src.parcel_service.core.config import RedisSettings


def create_redis_pool(settings: RedisSettings, db:int) -> redis.Redis:
    """
    Создаёт пул соединений Redis с учётом настроек и номера базы данных.

    :param settings: Настройки подключения к Redis (URL, лимиты, таймауты и т.д.).
    :type settings: RedisSettings
    :param db: Номер базы данных Redis (например, 0, 1, 2...).
    :type db: int
    :return: Асинхронный клиент Redis с созданным пулом соединений.
    :rtype: redis.Redis
    """
    parsed = urlparse(settings.url)
    parsed = parsed._replace(path=f"//{db}")
    redis_url = urlunparse(parsed)
    logger.debug(f"redis_url: {redis_url}")
    return redis.Redis.from_url(
        url = str(redis_url),
        max_connections = settings.max_connections,
        decode_responses = settings.decode_responses,
        socket_timeout=settings.socket_timeout,
        retry_on_timeout=settings.retry_on_timeout,
        health_check_interval=settings.health_check_interval
    )
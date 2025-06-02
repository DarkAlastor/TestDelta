import aiohttp
import json
from redis.asyncio import Redis
from loguru import logger

class CurrencyService:
    """
    Сервис для получения актуального курса USD к RUB с сайта ЦБ РФ.
    Использует Redis в качестве кеша для минимизации количества внешних запросов.
    """

    def __init__(self, redis: Redis):
        """
        Инициализирует сервис валют с зависимостью Redis.

        :param redis: Асинхронный клиент Redis для кеширования курсов валют.
        """
        self._redis = redis
        self._CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
        self._USD_CACHE_KEY = "usd_to_rub"
        self._CACHE_TTL_SECONDS = 3600

    async def get_usd_rate(self) -> float | None:
        """
        Получает курс доллара США (USD → RUB):
        - Сначала пытается взять из Redis.
        - Если нет, делает HTTP-запрос к ЦБ РФ и кеширует результат.

        :return: Курс USD → RUB как float, либо None при ошибке.
        :rtype: float | None
        """
        logger.debug("Entering get_usd_rate()")
        try:
            cached = await self._redis.get(self._USD_CACHE_KEY)
            logger.debug("USD rate retrieved from Redis cache: {}", cached)
            if cached:
                return float(cached)
        except Exception as e:
            logger.warning("Redis access failed: {}", str(e))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._CBR_URL, ssl=False) as resp:
                    logger.debug("HTTP response status from CBR: {}", resp.status)
                    if resp.status != 200:
                        raise RuntimeError("Failed to fetch USD rate")

                    text = await resp.text()
                    logger.debug("Raw response from CBR (truncated): {}...", text[:300])

                    try:
                        data = json.loads(text)
                    except Exception as json_err:
                        logger.error("Failed to parse JSON from CBR: {}", str(json_err))
                        return None

                    usd_info = data.get("Valute", {}).get("USD")
                    if not usd_info:
                        raise ValueError("USD not found in CBR response")

                    rate = usd_info["Value"]
                    logger.info("Fetched USD rate from CBR: {}", rate)

                    await self._redis.set(self._USD_CACHE_KEY, str(rate), ex=self._CACHE_TTL_SECONDS)
                    logger.debug("Cached USD rate in Redis: {} (TTL={}s)", rate, self._CACHE_TTL_SECONDS)
                    return rate

        except Exception as e:
            logger.error("Failed to fetch USD rate: {}", str(e))
            return None


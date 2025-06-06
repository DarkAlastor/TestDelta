from typing import Type, Dict
from loguru import logger
from redis import Redis
from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy import update, insert, select
from src.delivery_calculation_worker.db.sql.models import Parcel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from src.delivery_calculation_worker.services.currency import CurrencyService


class BaseStrategy(ABC):
    """
    Абстрактный базовый класс для стратегий обработки событий доставки.
    Каждая стратегия реализует метод `handle`, который принимает event-данные.
    """
    def __init__(self, session: AsyncSession, mongo_db: AsyncIOMotorDatabase, redis: Redis):
        """
        :param session: Асинхронная сессия SQLAlchemy.
        :param mongo_db: MongoDB клиент.
        :param redis: Redis клиент.
        """
        self.session = session
        self.mongo_db = mongo_db
        self.redis = redis

    @abstractmethod
    async def handle(self, data: dict):
        """
        Обрабатывает входящее событие.

        :param data: Словарь с данными события.
        """
        pass

class ParcelRegisteredStrategy(BaseStrategy):
    """
    Стратегия обработки события 'parcel.registered' — расчёт цены доставки и сохранение посылки.
    """
    def __init__(self, session, mongo_db, redis):
        super().__init__(session, mongo_db, redis)
        self.currency = CurrencyService(redis=redis)

    async def handle(self, event: dict) -> None:
        logger.debug("Calculating delivery for event: {}", event)

        parcel_data = event.get("payload")
        if not parcel_data:
            logger.warning("Empty payload in event")
            return

        try:
            usd_to_rub = await self.currency.get_usd_rate()
        except Exception as e:
            logger.warning("Could not fetch USD rate: {}", e)
            usd_to_rub = None

        parcel_id = parcel_data["parcel_id"]
        weight = parcel_data["weight_kg"]
        cost_usd = parcel_data["cost_adjustment_usd"]

        delivery_price = None
        if usd_to_rub:
            delivery_price = (weight * 0.5 + cost_usd * 0.01) * usd_to_rub

        # Проверяем: если уже есть, то просто выходим
        result = await self.session.execute(select(Parcel).where(Parcel.id == parcel_id))
        parcel = result.scalar_one_or_none()
        if parcel is not None:
            logger.info("Parcel {} already exists — skipping insert.", parcel_id)
            return

        # Вставляем новую посылку
        new_parcel = Parcel(
            id=parcel_id,
            session_id=parcel_data["session_id"],
            name=parcel_data["name"],
            weight_kg=weight,
            type_id=parcel_data["type_id"],
            cost_adjustment_usd=cost_usd,
            delivery_price_rub=delivery_price
        )
        self.session.add(new_parcel)
        await self.session.commit()
        logger.info("Inserted new parcel {} with delivery price: {}", parcel_id, delivery_price)

        # Запись в MongoDB лог, только если delivery_price посчитан
        if delivery_price is not None:
            log_doc = {
                "parcel_id": parcel_id,
                "type_id": parcel_data["type_id"],
                "session_id": parcel_data["session_id"],
                "calculated_price": delivery_price,
                "calculated_at": datetime.utcnow(),
            }
            await self.mongo_db["calculations"].insert_one(log_doc)
            logger.info("Logged calculation to MongoDB for parcel {}", parcel_id)


class ParcelRecalculateStrategy(BaseStrategy):
    """
    Стратегия для перерасчёта стоимости доставки для всех посылок с пустым `delivery_price_rub`.
    """
    def __init__(self, session, mongo_db, redis):
        super().__init__(session, mongo_db, redis)
        self.currency = CurrencyService(redis=redis)

    async def handle(self, event: dict) -> None:
        logger.debug("Recalculating delivery for event: {}", event)

        try:
            usd_to_rub = await self.currency.get_usd_rate()
        except Exception as e:
            logger.error("Could not fetch USD rate: {}", e)
            return

        if not usd_to_rub:
            logger.warning("USD rate not available — aborting recalculation")
            return

        # Найти все посылки с пустым delivery_price_rub
        result = await self.session.execute(
            select(Parcel).where(Parcel.delivery_price_rub.is_(None))
        )
        parcels = result.scalars().all()

        if not parcels:
            logger.info("No parcels found with missing delivery_price_rub.")
            return

        logger.info("Found {} parcels for recalculation.", len(parcels))

        updated_count = 0

        for parcel in parcels:
            weight = parcel.weight_kg
            cost_usd = parcel.cost_adjustment_usd

            delivery_price = (weight * 0.5 + cost_usd * 0.01) * usd_to_rub
            parcel.delivery_price_rub = delivery_price

            updated_count += 1

            #Лог в MongoDB (если нужно)
            await self.mongo_db["calculations"].update_one(
                {"parcel_id": parcel.id},
                {
                    "$set": {
                        "session_id": parcel.session_id,
                        "type_id": parcel.type_id,
                        "calculated_price": delivery_price,
                        "calculated_at": datetime.utcnow(),
                        "recalculated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )


        await self.session.commit()
        logger.info("Recalculated and updated {} parcels.", updated_count)


STRATEGY_REGISTRY: Dict[str, Type[BaseStrategy]] = {
    "parcel.registered": ParcelRegisteredStrategy,
    "parcel.recalculate": ParcelRecalculateStrategy,
}
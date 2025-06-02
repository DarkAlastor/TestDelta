import asyncio
from loguru import logger
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from aio_pika.exceptions import AMQPConnectionError

from src.outbox_publisher.core.container import AppContainer
from src.outbox_publisher.db.models import OutboxEvent
from src.outbox_publisher.core.config import AppPublisher


async def run_outbox_loop(settings: AppPublisher):
    """
    Запускает бесконечный цикл публикации событий из таблицы Outbox в RabbitMQ.

    Функция выполняет следующие шаги:
    1. Получает batch необработанных событий (`applied=False`) с блокировкой `SKIP LOCKED`.
    2. Публикует каждое событие в RabbitMQ с использованием `event_type` в качестве `routing_key`.
    3. Обновляет успешно отправленные события: помечает как `applied=True` и сохраняет `published_at`.
    4. При потере соединения с RabbitMQ делает паузу и повторяет попытку позже.

    :param settings: Настройки публикатора событий, включая размер batch и интервал ожидания.
    :type settings: AppPublisher
    """

    logger.info("Outbox publisher loop started", sleep_interval=settings.sleep_interval, batch_size=settings.batch_size)

    while True:
        # Получаем новую сессию из session factory
        async with AppContainer.session_factory() as session:

            # Читаем batch с блокировкой
            try:
                async with session.begin():
                    stmt = (
                        select(OutboxEvent)
                        .where(OutboxEvent.applied == False)
                        .order_by(OutboxEvent.created_at)
                        .limit(settings.batch_size)
                        .with_for_update(skip_locked=True)
                    )
                    result = await session.execute(stmt)
                    events = result.scalars().all()
            except SQLAlchemyError as e:
                logger.warning("Failed to fetch outbox events from DB", error=str(e))
                await asyncio.sleep(5)
                continue

            if not events:
                logger.debug("No new events found. Sleeping...", interval=settings.sleep_interval)
                await asyncio.sleep(settings.sleep_interval)
                continue

            logger.info("Fetched events for publishing", count=len(events))
            success_ids = []

            # Обрабатываем события (отправляем в RabbitMQ)
            for event in events:
                try:
                    logger.debug("Publishing event", event_id=event.id, event_type=event.event_type)
                    await AppContainer.rabbitmq_publisher.publish(
                        message_body={"payload": event.payload, "event_type": event.event_type},
                        routing_key=event.event_type
                    )
                    success_ids.append(event.id)
                    logger.info("Event published successfully", event_id=event.id)

                except AMQPConnectionError as e:
                    logger.warning(
                        "RabbitMQ connection lost. Will retry.",
                        error=str(e),
                        sleep_interval=settings.sleep_interval
                    )
                    break  # прерываем batch и даём системе время переподключиться

                except Exception as e:
                    logger.error("Failed to publish event", event_id=event.id, error=str(e))

            # Обновляем только успешно отправленные
            if success_ids:
                async with session.begin():
                    await session.execute(
                        update(OutboxEvent)
                        .where(OutboxEvent.id.in_(success_ids))
                        .values(
                            applied=True,
                            published_at=datetime.now(timezone.utc)
                        )
                    )
                    logger.info("Marked events as applied", ids=success_ids)

        await asyncio.sleep(settings.sleep_interval)


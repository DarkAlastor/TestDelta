from uuid import uuid4
from loguru import logger

from src.parcel_service.domain.interfaces.repository import IOutboxEventRepository
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase, TDeps
from src.parcel_service.infrastructure.db.sql.models import OutboxEvent
from src.parcel_service.domain.constants.events import EventType
from src.parcel_service.domain.exceptions.domain_error import OutboxDuplicateError, OutboxPersistenceError



class DebugRecalculateUseCase(IUseCase[None, None, None]):
    """
    Use case для генерации события пересчёта стоимости доставки и записи его в outbox.

    Реализует шаблон Outbox Pattern — событие записывается в таблицу outbox
    для последующей надёжной публикации во внешние системы.
    """

    async def __call__(self, dto: None, uow: IUnitOfWork, deps: TDeps = None) -> None:
        """
        Генерирует событие типа `PARCEL_RECALCULATE` и добавляет его в outbox.

        :param dto: Не используется (None).
        :type dto: None
        :param uow: Unit of Work для управления транзакциями и доступом к репозиториям.
        :type uow: IUnitOfWork
        :param deps: Не используется, зарезервировано для внешних зависимостей.
        :type deps: TDeps or None

        :return: None
        :rtype: None
        """
        try:
            outbox_event = OutboxEvent(
                id=str(uuid4()),
                event_type=EventType.PARCEL_RECALCULATE,
            )
            logger.debug("Сгенерировано событие OutboxEvent | id={} type={}", outbox_event.id, outbox_event.event_type)

            async with uow:
                repo_outbox = await uow.get_repo(IOutboxEventRepository)
                await repo_outbox.add(outbox_event)
                logger.info("Событие успешно добавлено в Outbox | id={}", outbox_event.id)


        except OutboxDuplicateError:
            logger.warning("Дубликат OutboxEvent ID | id={} type={}", outbox_event.id, outbox_event.event_type)
            raise

        except OutboxPersistenceError:
            logger.error("Ошибка БД при добавлении OutboxEvent | id={}", outbox_event.id)
            raise

        except Exception as e:
            logger.exception("Непредвиденная ошибка в DebugRecalculateUseCase | id={} | error={}", outbox_event.id, str(e))
            raise
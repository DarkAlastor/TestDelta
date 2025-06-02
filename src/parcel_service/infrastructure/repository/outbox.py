from typing import Optional
from loguru import logger

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.parcel_service.infrastructure.db.sql.models import OutboxEvent
from src.parcel_service.domain.interfaces.repository import IOutboxEventRepository

from src.parcel_service.domain.exceptions.domain_error import OutboxDuplicateError, OutboxPersistenceError

from .registry import RepositoryRegistry

@RepositoryRegistry.register(IOutboxEventRepository)
class OutboxEventRepository(IOutboxEventRepository):
    """
    Репозиторий для работы с сущностями OutboxEvent.

    Используется в реализации Outbox Pattern — хранение событий до публикации в брокер.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Конструктор репозитория OutboxEvent.

        :param session: Асинхронная сессия SQLAlchemy.
        :type session: AsyncSession
        """
        super().__init__(session)

    async def add(self, event: OutboxEvent) -> None:
        """
        Добавляет событие в сессию базы данных (в таблицу outbox).

        :param event: Событие, которое необходимо сохранить.
        :type event: OutboxEvent
        """
        try:
            logger.debug("Adding OutboxEvent | id={} type={}", event.id, event.event_type)
            self._session.add(event)
        except IntegrityError as e:
            logger.warning("Duplicate OutboxEvent ID detected | id={} type={} | error={}", event.id, event.event_type,str(e))
            raise OutboxDuplicateError()
        except Exception as e:
            logger.error("Failed to add OutboxEvent | id={} type={} | error={}", event.id, event.event_type, str(e))
            raise OutboxPersistenceError()

    async def get_by_id(self, parcel_id: str) -> Optional[OutboxEvent]:
        """
        Получает запись из таблицы outbox по его идентификатору.

        :param parcel_id: Идентификатор события.
        :type parcel_id: str
        :return: Найденное событие или None.
        :rtype: Optional[OutboxEvent]
        """
        try:
            logger.debug("Fetching OutboxEvent by | id={}", parcel_id)
            stmt = select(OutboxEvent).where(OutboxEvent.id == parcel_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Непредвиденная ошибка в OutboxEvent | id={} | error={}", parcel_id, str(e))
            raise

    async def _log_identity_debug(self) -> int:
        """
        Отладочный метод для возврата внутреннего идентификатора объекта (id(self)).

        :return: Уникальный ID экземпляра.
        :rtype: int
        """
        return id(self)
from typing import List, Optional
from loguru import logger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.parcel_service.infrastructure.db.sql.models import ParcelType
from src.parcel_service.domain.interfaces.repository import IParcelTypeRepository

from .registry import RepositoryRegistry

@RepositoryRegistry.register(IParcelTypeRepository)
class ParcelTypeRepository(IParcelTypeRepository):
    """
    Репозиторий для работы со справочником типов посылок (`ParcelType`).

    Зарегистрирован как реализация интерфейса `IParcelTypeRepository`.

    :param session: Асинхронная SQLAlchemy-сессия.
    :type session: AsyncSession
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def _log_identity_debug(self) -> int:
        """
        Отладочный метод, возвращающий уникальный идентификатор экземпляра.

        :return: `id(self)`
        :rtype: int
        """
        return id(self)

    async def list_all(self) -> Optional[List[ParcelType]]:
        """
        Получает все доступные типы посылок из таблицы `parcel_types`.

        :return: Список типов посылок.
        """
        try:
            stmt = select(ParcelType).order_by(ParcelType.id)
            result = await self._session.execute(stmt)
            types = list(result.scalars().all())

            logger.info("Загружены типы посылок | count={}", len(types))
            return types

        except SQLAlchemyError as e:
            logger.error("Ошибка при получении типов посылок из БД | {}", str(e))
            raise

        except Exception as e:
            logger.exception("Непредвиденная ошибка при получении типов посылок | {}", str(e))
            raise

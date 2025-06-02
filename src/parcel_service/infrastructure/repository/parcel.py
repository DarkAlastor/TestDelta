from typing import Optional
from loguru import logger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.parcel_service.domain.interfaces.repository import IParcelRepository
from src.parcel_service.infrastructure.db.sql.models import Parcel, Company
from src.parcel_service.infrastructure.repository.registry import RepositoryRegistry
from src.parcel_service.domain.exceptions.domain_error import CompanyNotFoundError
from src.parcel_service.domain.exceptions.domain_error import ParcelNotFoundError, ParcelAlreadyExistsError

@RepositoryRegistry.register(IParcelRepository)
class ParcelRepository(IParcelRepository):
    """
    Реализация репозитория для работы с сущностью Parcel.

    Зарегистрирована через `RepositoryRegistry` как реализация интерфейса `IParcelRepository`.

    :param session: Асинхронная сессия SQLAlchemy.
    :type session: AsyncSession
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def _log_identity_debug(self) -> int:
        """
        Отладочный метод, возвращающий внутренний ID объекта репозитория.

        :return: Уникальный идентификатор экземпляра (id(self)).
        :rtype: int
        """
        return id(self)

    async def add(self, parcel: Parcel) -> None:
        """
        Добавляет новую посылку в текущую сессию БД.

        :param parcel: Объект посылки.
        :type parcel: Parcel
        :raises ParcelAlreadyExistsError: Если посылка с таким ID уже существует.
        """
        try:
            logger.debug("Добавляется посылка | parcel_id={}", parcel.id)
            self._session.add(parcel)
        except IntegrityError as e:
            logger.warning("Посылка уже существует | parcel_id={} | error={}", parcel.id, str(e))
            raise ParcelAlreadyExistsError()
        except SQLAlchemyError as e:
            logger.error("Ошибка при добавлении посылки | parcel_id={} | error={}", parcel.id, str(e))
            raise

    async def get_by_id(self, parcel_id: str) -> Optional[Parcel]:
        """
        Получает посылку по её уникальному идентификатору.

        :param parcel_id: Идентификатор посылки.
        :type parcel_id: str
        :return: Объект Parcel или None, если не найден.
        :rtype: Optional[Parcel]
        """
        try:
            stmt = select(Parcel).where(Parcel.id == parcel_id)
            result = await self._session.execute(stmt)
            parcel = result.scalar_one_or_none()
            if parcel is None:
                logger.warning("Посылка не найдена | parcel_id={}", parcel_id)
            return parcel
        except Exception as e:
            logger.error("Непредвиденная ошибка в Parcel | id={} | error={}", parcel_id, str(e))
            raise

    async def bind_company_if_unset(self, parcel_id: str, company_id: int) -> Optional[bool]:
        """
        Привязывает компанию к посылке, если она ещё не была привязана.

        :param parcel_id: Идентификатор посылки.
        :type parcel_id: str
        :param company_id: Идентификатор транспортной компании.
        :type company_id: int
        :return: True, если обновление прошло успешно (привязка выполнена), иначе False.
        :rtype: bool
        """
        try:
            logger.debug("Пытаемся заблокировать посылку для обновления | parcel_id={}", parcel_id)

            logger.debug("Проверка существования компании | company_id={}", company_id)
            company_stmt = select(Company.id).where(Company.id == company_id)
            company_result = await self._session.execute(company_stmt)
            if company_result.scalar_one_or_none() is None:
                logger.warning("Компания с таким ID не найдена | company_id={}", company_id)
                raise CompanyNotFoundError()

            stmt_select = select(Parcel).where(Parcel.id == parcel_id).with_for_update()
            result = await self._session.execute(stmt_select)
            parcel = result.scalar_one_or_none()


            if parcel is None:
                logger.warning("Посылка не найдена при попытке привязки компании | parcel_id={}", parcel_id)
                return None

            if parcel.company_id is not None:
                logger.warning("Компания уже привязана к посылке | parcel_id={} company_id={}", parcel_id, parcel.company_id)
                return False

            parcel.company_id = company_id
            logger.info("Компания успешно привязана к посылке | parcel_id={} company_id={}", parcel_id, company_id)
            return True

        except Exception as e:
            logger.error("Ошибка при попытке привязки компании | parcel_id={} company_id={} error = {}", parcel_id, company_id, e)
            raise
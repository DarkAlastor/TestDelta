from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, Type, TypeVar, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.parcel_service.infrastructure.db.sql.models import OutboxEvent, Parcel, ParcelType


class IBaseRepository(ABC):
    """
    Базовый интерфейс для всех репозиториев.

    :param session: Асинхронная сессия SQLAlchemy.
    :type session: AsyncSession
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @abstractmethod
    async def _log_identity_debug(self) -> int:
        """
        Отладочный метод, возвращающий id текущего объекта.

        :return: Уникальный идентификатор экземпляра.
        :rtype: int
        """
        pass


TRepo = TypeVar("TRepo", bound=IBaseRepository)
TImpl = TypeVar("TImpl", bound=IBaseRepository)
TInterface = TypeVar("TInterface", bound=IBaseRepository)

class IRepositoryFactory(Protocol):
    """
    Интерфейс фабрики репозиториев.
    """

    async def get(self, repo_interface: Type[TInterface],  session:AsyncSession) -> TImpl:
        """
        Возвращает реализацию репозитория по интерфейсу.

        :param repo_interface: Интерфейс репозитория.
        :type repo_interface: Type[TInterface]
        :param session: Асинхронная сессия SQLAlchemy.
        :type session: AsyncSession
        :return: Реализация указанного интерфейса.
        :rtype: TImpl
        """
        pass

class IParcelRepository(IBaseRepository):
    """
    Интерфейс репозитория для работы с сущностью Parcel (посылка).
    """

    @abstractmethod
    async def add(self, parcel: Parcel) -> None:
        """
        Добавляет новую посылку.

        :param parcel: Объект посылки.
        :type parcel: Parcel
        """
        pass

    @abstractmethod
    async def get_by_id(self, parcel_id: str) -> Optional[Parcel]:
        """
        Получает посылку по её ID.

        :param parcel_id: Идентификатор посылки.
        :type parcel_id: str
        :return: Объект посылки или None.
        :rtype: Optional[Parcel]
        """
        pass

    @abstractmethod
    async def bind_company_if_unset(self, parcel_id: str, company_id: int) -> Optional[bool]:
        """
        Привязывает компанию к посылке, если она ещё не привязана.

        :param parcel_id: ID посылки.
        :type parcel_id: str
        :param company_id: ID транспортной компании.
        :type company_id: int
        :return: True, если привязка выполнена успешно; иначе False.
        :rtype: bool
        """
        pass


class IOutboxEventRepository(IBaseRepository):
    """
    Интерфейс репозитория для работы с событиями Outbox.
    """

    @abstractmethod
    async def add(self, event: OutboxEvent) -> None:
        """
        Добавляет событие в Outbox.

        :param event: Событие для публикации.
        :type event: OutboxEvent
        """
        pass

    @abstractmethod
    async def get_by_id(self, parcel_id: str) -> OutboxEvent:
        """
         Получает запись из Outbox по ID посылки.

         :param parcel_id: Идентификатор посылки.
         :type parcel_id: str
         :return: Событие из Outbox.
         :rtype: OutboxEvent
         """
        pass

class IParcelCombinedRepository(IBaseRepository):
    """
     Интерфейс агрегированного репозитория для работы с посылками и связанными сущностями Outbox Parcel.
     """

    @abstractmethod
    async def list_paginated(self,session_id: str, limit: int, offset: int, type_id: Optional[int]=None) -> List[Tuple[str, str]]:
        """
        Получает постраничный список ID посылок и их типов по session_id.

        :param session_id: Идентификатор сессии.
        :type session_id: str
        :param limit: Кол-во записей на странице.
        :type limit: int
        :param offset: Смещение (offset) от начала.
        :type offset: int
        :return: Список кортежей (parcel_id, type_name).
        :rtype: List[Tuple[str, str]]
        """
        pass

    @abstractmethod
    async def get_parcels_by_ids(self, ids: List[str]) -> List[Parcel]:
        """
        Получает список посылок по их ID.

        :param ids: Список идентификаторов посылок.
        :type ids: List[str]
        :return: Список объектов Parcel.
        :rtype: List[Parcel]
        """
        pass

    @abstractmethod
    async def get_outbox_by_parcel_ids(self, ids: List[str]) -> List[OutboxEvent]:
        """
        Получает события Outbox по списку ID посылок.

        :param ids: Список идентификаторов посылок.
        :type ids: List[str]
        :return: Список объектов OutboxEvent.
        :rtype: List[OutboxEvent]
        """
        pass

    @abstractmethod
    async def count(self, session_id: str, type_id: Optional[int]=None, has_delivery_price: bool = False) -> int:
        """
        Считает количество посылок для сессии.

        :param session_id: Идентификатор сессии.
        :type session_id: str
        :return: Общее количество посылок.
        :rtype: int
        """
        pass

class IParcelTypeRepository(IBaseRepository):
    """
    Интерфейс репозитория для работы с типами посылок.
    """

    @abstractmethod
    async def list_all(self) -> Optional[List[ParcelType]]:
        """
        Получает все типы посылок из справочника.

        :return: Список типов посылок.
        :rtype: List[ParcelType]
        """
        pass

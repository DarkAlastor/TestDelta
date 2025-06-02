from abc import ABC, abstractmethod
from typing import Callable, Type

from sqlalchemy.ext.asyncio import AsyncSession

from src.parcel_service.domain.interfaces.repository import IRepositoryFactory, TRepo


class IUnitOfWork(ABC):
    """
    Интерфейс паттерна Unit of Work для управления транзакциями и доступом к репозиториям.

    Используется для координации работы между несколькими репозиториями с сохранением атомарности операций.

    :param session_factory: Фабрика для создания новых сессий SQLAlchemy.
    :type session_factory: Callable[[], AsyncSession]
    :param repository_factory: Фабрика для получения репозиториев.
    :type repository_factory: IRepositoryFactory
    """

    def __init__(self, session_factory: Callable[[], AsyncSession], repository_factory: IRepositoryFactory) -> None:
        self._session_factory = session_factory
        self._repository_factory = repository_factory

    @abstractmethod
    async def get_repo(self, repo_type: Type[TRepo]) -> TRepo:
        """
        Возвращает репозиторий по типу интерфейса.

        :param repo_type: Тип запрашиваемого интерфейса репозитория.
        :type repo_type: Type[TRepo]
        :return: Экземпляр запрошенного репозитория.
        :rtype: TRepo
        """
        pass

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        """
        Вход в асинхронный контекст Unit of Work.

        :return: Экземпляр IUnitOfWork.
        :rtype: IUnitOfWork
        """
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> "IUnitOfWork":
        """
        Выход из асинхронного контекста Unit of Work.

        :param exc_type: Тип исключения (если есть).
        :param exc_val: Объект исключения (если есть).
        :param exc_tb: Трассировка исключения (если есть).
        :return: Экземпляр IUnitOfWork.
        :rtype: IUnitOfWork
        """
        pass

    @abstractmethod
    async def _commit(self) -> None:
        """
        Подтверждает транзакцию.
        """
        pass

    @abstractmethod
    async def _rollback(self) -> None:
        """
        Откатывает транзакцию.
        """
        pass
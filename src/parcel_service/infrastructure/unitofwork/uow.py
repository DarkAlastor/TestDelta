from typing import Callable, Type

from sqlalchemy.ext.asyncio import AsyncSession

from src.parcel_service.domain.interfaces.repository import IRepositoryFactory, TRepo
from src.parcel_service.domain.interfaces.uow import IUnitOfWork


class UnitOfWork(IUnitOfWork):
    """
    Реализация паттерна Unit of Work.

    Управляет жизненным циклом SQLAlchemy-сессии и кэширует репозитории в пределах одной транзакции.

    :param session_factory: Фабрика для создания новых асинхронных сессий.
    :type session_factory: Callable[[], AsyncSession]
    :param repository_factory: Фабрика для создания репозиториев.
    :type repository_factory: IRepositoryFactory
    """

    __slots__ = ("_cache", "_repository_factory", "_session", "_session_factory")

    def __init__(self, session_factory: Callable[[], AsyncSession], repository_factory: IRepositoryFactory) -> None:
        super().__init__(session_factory, repository_factory)
        self._session: AsyncSession | None = None
        self._cache = {}

    async def get_repo(self, repo_type: Type[TRepo]) -> TRepo:
        """
        Возвращает репозиторий по типу интерфейса. Кеширует внутри Unit of Work.

        :param repo_type: Тип запрашиваемого репозитория.
        :type repo_type: Type[TRepo]
        :return: Экземпляр репозитория.
        :rtype: TRepo
        """
        if repo_type not in self._cache:
            self._cache[repo_type] = await self._repository_factory.get(repo_type, self._session)
        return self._cache[repo_type]

    async def __aenter__(self) -> "UnitOfWork":
        """
        Вход в асинхронный контекст Unit of Work (инициализирует сессию).

        :return: Текущий экземпляр Unit of Work.
        :rtype: UnitOfWork
        """
        self._session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Выход из асинхронного контекста Unit of Work.

        Выполняет коммит, если не было исключения, иначе — откат транзакции.

        :param exc_type: Тип исключения (если было).
        :param exc_val: Значение исключения.
        :param exc_tb: Трассировка исключения.
        """
        if exc_type:
            await self._rollback()
        else:
            await self._commit()

    async def _commit(self) -> None:
        """
        Выполняет коммит текущей транзакции.
        """
        await self._session.commit()

    async def _rollback(self) -> None:
        """
        Выполняет откат текущей транзакции.
        """
        await self._session.rollback()
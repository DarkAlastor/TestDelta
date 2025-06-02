from typing import Dict, Type

from sqlalchemy.ext.asyncio import AsyncSession

from src.parcel_service.domain.interfaces.repository import IRepositoryFactory, TImpl, TInterface


# Фабрикак для создания репозиториев
class RepositoryFactory(IRepositoryFactory):
    """
    Фабрика для создания экземпляров репозиториев на основе интерфейсов.

    Использует заранее определённый реестр (registry), сопоставляющий интерфейсы с их реализациями.

    :param registry: Словарь, где ключ — интерфейс репозитория, а значение — соответствующая реализация.
    :type registry: Dict[Type[TInterface], Type[TImpl]]
    """

    def __init__(self, registry: Dict[Type[TInterface], Type[TImpl]]) -> None:
        self._registry = registry

    async def get(self, repo_interface: Type[TInterface],  session: AsyncSession) -> TImpl:
        """
        Получает реализацию репозитория по интерфейсу и переданной сессии.

        :param repo_interface: Класс-интерфейс репозитория.
        :type repo_interface: Type[TInterface]
        :param session: Асинхронная сессия SQLAlchemy.
        :type session: AsyncSession
        :raises ValueError: Если реализация для указанного интерфейса не найдена в реестре.
        :return: Экземпляр реализации репозитория.
        :rtype: TImpl
        """
        repo_clas = self._registry.get(repo_interface)
        if repo_clas is None:
            raise ValueError(f"No repo found for {repo_interface}")
        return repo_clas(session)
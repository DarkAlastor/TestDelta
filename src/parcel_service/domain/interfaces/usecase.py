from abc import ABC
from typing import Generic, TypeVar

from src.parcel_service.domain.interfaces.uow import IUnitOfWork

Input = TypeVar("Input")
Output = TypeVar("Output")
TDeps = TypeVar("TDeps")

class IUseCase(ABC, Generic[Input, Output, TDeps]):
    """
    Интерфейс для реализации бизнес-логики (Use Case) в системе.

    Поддерживает передачу входных данных, зависимостей и Unit of Work для работы с БД.

    :param Input: Тип входных данных.
    :param Output: Тип возвращаемого результата.
    :param TDeps: Тип внешних зависимостей (например, брокеры, API, кэш и т.д.).
    """

    async def __call__(self, dto: Input, uow: IUnitOfWork, deps: TDeps) -> Output:
        """
        Выполняет бизнес-логику use case.

        :param dto: Входные данные.
        :type dto: Input
        :param uow: Экземпляр Unit of Work для работы с репозиториями и транзакциями.
        :type uow: IUnitOfWork
        :param deps: Дополнительные зависимости, необходимые для выполнения use case.
        :type deps: TDeps
        :return: Результат выполнения use case.
        :rtype: Output
        """
        pass
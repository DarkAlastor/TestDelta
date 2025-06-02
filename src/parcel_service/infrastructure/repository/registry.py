from typing import ClassVar, Dict, Type

from src.parcel_service.domain.interfaces.repository import IBaseRepository


# реестр репозиториев
class RepositoryRegistry:
    """
    Реестр соответствий интерфейсов репозиториев и их реализаций.

    Используется для регистрации реализаций репозиториев с последующим доступом через фабрику `RepositoryFactory`.

    :cvar _map: Внутреннее хранилище соответствий интерфейс → реализация.
    :vartype _map: ClassVar[Dict[Type[IBaseRepository], Type[IBaseRepository]]]
    """
    _map: ClassVar[Dict[Type[IBaseRepository], Type[IBaseRepository]]] = {}

    @classmethod
    def register(cls, interface: Type[IBaseRepository]):
        """
        Регистрирует реализацию репозитория для указанного интерфейса.

        Пример использования:
        >>> @RepositoryRegistry.register(IParcelRepository)
        ... class ParcelRepository(IParcelRepository):
        ...     ...
        и подключай файл в __init__ repository
        :param interface: Интерфейс репозитория.
        :type interface: Type[IBaseRepository]
        :raises TypeError: Если реализация не наследует указанный интерфейс.
        :return: Декоратор, регистрирующий реализацию.
        :rtype: Callable[[Type[IBaseRepository]], Type[IBaseRepository]]
        """
        def decorator(impl: Type[IBaseRepository]):
            if not issubclass(impl, interface):
                raise TypeError(f"{impl} does not implement {interface}")
            cls._map[interface] = impl
            return impl

        return decorator

    @staticmethod
    def get() -> dict[Type[IBaseRepository], Type[IBaseRepository]]:
        """
        Возвращает копию зарегистрированного реестра интерфейсов и реализаций.

        :return: Словарь интерфейсов и их реализаций.
        :rtype: Dict[Type[IBaseRepository], Type[IBaseRepository]]
        """
        return RepositoryRegistry._map.copy()
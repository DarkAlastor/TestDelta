from src.parcel_service.domain.interfaces.usecase import IUseCase
from src.parcel_service.application.use_cases.parcels.get_parcels_for_id import GetParcelsForIdUseCase
from src.parcel_service.application.use_cases.parcels.registry_parcel import RegistryParcelUseCase
from src.parcel_service.application.use_cases.parcels.get_parcels_list import GetParcelsListUseCase
from src.parcel_service.application.use_cases.parcels.get_all_type_parcels import GetAllTypeParcelsUseCase
from src.parcel_service.application.use_cases.parcels.bind_company import BindCompanyUseCase


def get_uc_registry() -> IUseCase:
    """
    Use case для регистрации новой посылки.

    :return: Экземпляр use case для регистрации новой посылки.
    :rtype: IUseCase
    """
    return RegistryParcelUseCase()


def get_uc_parcels_for_id() -> IUseCase:
    """
    Use case для получения информации о посылке по её ID.

    :return: Экземпляр use case для получения информации по ID посылки.
    :rtype: IUseCase
    """
    return GetParcelsForIdUseCase()


def get_uc_parcels_list_for_session_id() -> IUseCase:
    """
    Use case для получения списка посылок по session_id с поддержкой фильтрации и пагинации.

    :return: Экземпляр use case для получения списка посылок по session_id.
    :rtype: IUseCase
    """
    return GetParcelsListUseCase()


def get_uc_parcels_all_types() -> IUseCase:
    """
    Use case для получения всех типов посылок.

    :return: Экземпляр use case для получения списка всех типов посылок.
    :rtype: IUseCase
    """
    return GetAllTypeParcelsUseCase()


def get_uc_bind_compony() -> IUseCase:
    """
    Use case для привязки посылки к транспортной компании.

    :return: Экземпляр use case для привязки посылки к транспортной компании.
    :rtype: IUseCase
    """
    return BindCompanyUseCase()


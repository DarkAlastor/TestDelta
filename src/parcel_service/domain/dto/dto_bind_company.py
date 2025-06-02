from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class BindCompanyData:
    """
    Входные данные для привязки посылки к транспортной компании.

    :param parcel_id: Уникальный идентификатор посылки.
    :type parcel_id: str
    :param company_id: Идентификатор транспортной компании.
    :type company_id: int
    """
    parcel_id: str
    company_id: int


@dataclass(frozen=True, slots=True)
class BindCompanyResult:
    """
    Результат успешной привязки посылки к транспортной компании.

    :param message: Сообщение об успешной операции.
    :type message: str
    """
    message: str = "Parcel registered for company"
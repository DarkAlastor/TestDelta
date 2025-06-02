from typing import List
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParcelDetailQuery:
    """
    Запрос на получение детальной информации о конкретной посылке.

    :param parcel_id: Уникальный идентификатор посылки.
    :type parcel_id: str
    :param session_id: Идентификатор пользовательской сессии.
    :type session_id: str
    """
    parcel_id: str
    session_id: str

@dataclass(frozen=True, slots=True)
class ParcelDetailResult:
    """
    Детальная информация о посылке.

    :param parcel_id: Идентификатор посылки.
    :type parcel_id: str
    :param name: Название посылки.
    :type name: str
    :param weight_kg: Вес посылки в килограммах.
    :type weight_kg: float
    :param type_id: Идентификатор типа посылки.
    :type type_id: int
    :param cost_adjustment_usd: Стоимость содержимого в долларах США.
    :type cost_adjustment_usd: float
    :param delivery_price_rub: Стоимость доставки в рублях (или "Not calculated").
    :type delivery_price_rub: str
    """
    parcel_id: str
    name: str
    weight_kg: float
    type_id: int
    cost_adjustment_usd: float
    delivery_price_rub: str

@dataclass(frozen=True, slots=True)
class ParcelQueryList:
    """
    Запрос на получение списка посылок с возможностью фильтрации и пагинации.

    :param session_id: Идентификатор сессии.
    :type session_id: str
    :param type_id: Фильтр по типу посылки.
    :type type_id: int
    :param limit: Количество элементов на странице.
    :type limit: int
    :param offset: Смещение от начала списка (для пагинации).
    :type offset: int
    :param has_delivery_price: Фильтр по наличию рассчитанной стоимости доставки.
    :type has_delivery_price: bool
    """
    session_id: str
    type_id: int
    limit: int
    offset: int
    has_delivery_price: bool = False

@dataclass(frozen=True, slots=True)
class ParcelDetailQueryList:
    """
    Ответ на запрос списка посылок.

    :param items: Список посылок с полной информацией.
    :type items: List[ParcelDetailResult]
    :param total: Общее количество посылок, подходящих под условия запроса.
    :type total: int
    """
    items: List[ParcelDetailResult]
    total: int

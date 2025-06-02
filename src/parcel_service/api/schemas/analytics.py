from datetime import datetime
from typing import List

from pydantic import BaseModel


class DeliveryCostItem(BaseModel):
    """
    Представляет агрегированные данные по стоимости доставки для одного типа посылок.

    :param type: Название типа посылки (например, "одежда", "электроника").
    :type type: str

    :param total: Общая сумма доставки для данного типа (в рублях).
    :type total: float
    """
    type: int
    total: float


class AnalyticsResponse(BaseModel):
    """
    Ответ аналитического запроса, агрегирующий данные по доставке за определённую дату.

    :param date: Дата, за которую рассчитана аналитика.
    :type date: datetime

    :param group_by: Поле, по которому выполнена агрегация (например, "type").
    :type group_by: str

    :param items: Список агрегированных значений по типам.
    :type items: List[DeliveryCostItem]
    """
    date: datetime
    group_by: str
    items: List[DeliveryCostItem]
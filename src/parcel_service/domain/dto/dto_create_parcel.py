from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ParcelData:
    """
    Данные о посылке, используемые при регистрации и расчётах.

    :param parcel_id: Уникальный идентификатор посылки.
    :type parcel_id: str
    :param session_id: Идентификатор сессии пользователя.
    :type session_id: str
    :param name: Название посылки.
    :type name: str
    :param weight_kg: Вес посылки в килограммах.
    :type weight_kg: float
    :param type_id: Идентификатор типа посылки (ссылка на справочник типов).
    :type type_id: int
    :param cost_adjustment_usd: Стоимость содержимого в долларах США.
    :type cost_adjustment_usd: float
    :param delivery_price_rub: Стоимость доставки в рублях или строка `"Not calculated"`, если расчёт не произведён.
    :type delivery_price_rub: float or None
    """
    parcel_id: str
    session_id: str
    name: str
    weight_kg: float
    type_id: int
    cost_adjustment_usd: float
    delivery_price_rub: float | None = None

    def to_payload(self) -> dict:
        """
        Возвращает сериализованное представление данных для отправки во внешние системы
        (например, в Outbox, брокер сообщений, логи).

        :return: Словарь с безопасными и проверенными данными о посылке.
        :rtype: dict
        """
        return {
            "parcel_id": self.parcel_id,
            "session_id": self.session_id,
            "name": self.name,
            "weight_kg": self.weight_kg,
            "type_id": self.type_id,
            "cost_adjustment_usd": self.cost_adjustment_usd,
            "delivery_price_rub": self.delivery_price_rub,
        }

@dataclass(frozen=True, slots=True)
class ParcelResult:
    """
    Результат успешной регистрации посылки.

    :param parcel_id: Уникальный идентификатор зарегистрированной посылки.
    :type parcel_id: str
    :param message: Сообщение об успешной регистрации.
    :type message: str
    """
    parcel_id: str
    message: str = "Parcel registered"
from enum import Enum

class EventType(str, Enum):
    """
    Перечисление допустимых типов событий для обмена сообщениями через RabbitMQ.

    Используется для идентификации бизнес-событий в системе.

    Attributes
    --------
    PARCEL_REGISTERED : str
        Событие регистрации новой посылки (`"parcel.registered"`).
    PARCEL_RECALCULATE : str
        Событие запроса на пересчёт стоимости доставки (`"parcel.recalculate"`).
    """
    PARCEL_REGISTERED = "parcel.registered"
    PARCEL_RECALCULATE = "parcel.recalculate"

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ParcelType:
    """
    Тип посылки из справочника.

    :param id: Уникальный идентификатор типа посылки.
    :type id: int
    :param name: Название типа посылки (например, "одежда", "электроника").
    :type name: str
    """
    id: int
    name: str
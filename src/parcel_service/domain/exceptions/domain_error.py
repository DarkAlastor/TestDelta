class DomainError(Exception):
    """
    Базовое доменное исключение.

    Используется как родитель для всех исключений бизнес-логики в системе.
    """
    pass

class AccessDeniedError(DomainError):
    """
    Исключение, вызываемое при попытке доступа к недоступной посылке.

    :param message: Сообщение об ошибке.
    :type message: str
    """
    def __init__(self, message: str = "Access to parcel denied"):
        super().__init__(message)

class ParcelNotFoundError(DomainError):
    """
    Исключение, возникающее, если посылка не найдена.
    """
    def __init__(self):
        super().__init__("Parcel not found")

class ParcelAlreadyExistsError(DomainError):
    """
    Исключение, возникающее, если посылка не найдена.
    """
    def __init__(self):
        super().__init__("Parcel is existis")


class ParcelAlreadyBoundError(DomainError):
    """
    Исключение, возникающее, если посылка уже привязана к другой транспортной компании.

    :param message: Сообщение об ошибке.
    :type message: str
    """
    def __init__(self, message: str = "The parcel is already a sentence for another company"):
        super().__init__(message)

class OutboxDuplicateError(DomainError):
    """
    Ошибка дублирующей записи в Outbox (например, по id).
    """
    def __init__(self, message: str = "Duplicate OutboxEvent detected"):
        super().__init__(message)

class OutboxPersistenceError(DomainError):
    """
    Ошибка при сохранении события в Outbox (например, ошибка БД).
    """
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message)

class CompanyNotFoundError(DomainError):
    """
    Исключение, возникающее, если посылка не найдена.
    """
    def __init__(self):
        super().__init__("Transport company not found")
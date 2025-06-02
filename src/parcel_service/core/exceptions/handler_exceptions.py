from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger

from src.parcel_service.domain.exceptions.domain_error import (
    AccessDeniedError,
    DomainError,
    ParcelAlreadyBoundError,
    ParcelNotFoundError,
    OutboxPersistenceError,
    OutboxDuplicateError,
    ParcelAlreadyExistsError,
    CompanyNotFoundError
)

domain_status_map = {
    CompanyNotFoundError: 404,
    ParcelAlreadyBoundError: 409,
    AccessDeniedError: 403,
    ParcelNotFoundError: 404,
    ParcelAlreadyExistsError:409,
    OutboxDuplicateError: 409,
    OutboxPersistenceError: 500,  # можно также 503, если это transient error
}

# Обработчик бизнес-исключений
async def domain_error_handler(request: Request, exc: DomainError):
    """
    Обрабатывает бизнес-исключения, наследуемые от `DomainError`.

    Преобразует исключение в корректный HTTP-ответ с соответствующим статусом.

    :param request: Исходный HTTP-запрос.
    :type request: Request
    :param exc: Исключение бизнес-логики (напр. `ParcelNotFoundError`).
    :type exc: DomainError
    :return: Ответ с JSON-сообщением и статусом.
    :rtype: JSONResponse
    """
    status_code = domain_status_map.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"message": str(exc)}
    )


# Обработчик HTTP ошибок (FastAPI HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Обрабатывает стандартные HTTP-исключения FastAPI (например, `raise HTTPException(...)`).

    В лог добавляется информация о маршруте, методе, клиенте и деталях ошибки.

    :param request: Исходный HTTP-запрос.
    :type request: Request
    :param exc: Исключение FastAPI.
    :type exc: HTTPException
    :return: Ответ с JSON-сообщением и кодом ошибки.
    :rtype: JSONResponse
    """

    logger.error(
        "HTTP %s | %s %s | client_id=%s request_id=%s | detail=%s",
        exc.status_code,
        request.method,
        request.url.path,
        getattr(request.scope.get("request_meta") or object(), "client_id", "none"),
        getattr(request.scope.get("request_meta") or object(), "request_id", "none"),
        exc.detail
    )

    message = "Bad Request" if exc.status_code == 400 else exc.detail

    return JSONResponse(
        status_code=exc.status_code,
        content={"message": message}
    )

# Fallback: любая непойманная ошибка (500)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Fallback-обработчик для всех неперехваченных исключений (возвращает 500).

    Логирует ошибку как `exception`, включая трассировку.

    :param request: Исходный HTTP-запрос.
    :type request: Request
    :param exc: Произвольное необработанное исключение.
    :type exc: Exception
    :return: Ответ с сообщением об ошибке 500.
    :rtype: JSONResponse
    """
    # Отключить лог в проде, если нужно
    logger.exception("Unhandled internal error")

    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )
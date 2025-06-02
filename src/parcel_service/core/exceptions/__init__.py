from fastapi import FastAPI, HTTPException
from loguru import logger

from src.parcel_service.core.exceptions.handler_exceptions import (
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from src.parcel_service.domain.exceptions.domain_error import DomainError


def register_exceptions(app:FastAPI) -> None:
    """
    Регистрирует глобальные обработчики исключений для FastAPI-приложения.

    Включает:
    - Обработку бизнес-исключений (`DomainError`)
    - Обработку HTTP-исключений (`HTTPException`)
    - Обработку непредвиденных исключений (`Exception`)

    Все обработчики логируют информацию о произошедших ошибках.

    :param app: Экземпляр FastAPI-приложения, в которое регистрируются обработчики.
    :type app: FastAPI
    """
    logger.info("Reg exceptions")

    app.add_exception_handler(DomainError, domain_error_handler)
    logger.info("DomainError exception enabled")

    app.add_exception_handler(HTTPException, http_exception_handler)
    logger.info("HTTPException exception enabled")


    app.add_exception_handler(Exception, unhandled_exception_handler)
    logger.info("Exception exception enabled")
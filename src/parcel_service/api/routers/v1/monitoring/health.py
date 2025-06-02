from typing import Callable

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.parcel_service.api.deps.shared_deps import get_session_factory

router = APIRouter()

@router.get("/health", summary="Проверка здоровья сервера")
async def health() -> JSONResponse:
    """
    Простой health-check эндпоинт, показывающий, что сервер запущен.

    Используется для мониторинга доступности сервиса.

    :return: JSON с общим статусом "ok".
    :rtype: JSONResponse
    """
    return JSONResponse(status_code=200, content={
        "status": "ok",
        "service": "core-app"
    })

@router.get("/live", summary="Проверка живой ли сейчас сервер")
async def live() -> JSONResponse:
    """
    Live-check эндпоинт, подтверждающий, что приложение не упало и откликается.

    Для систем типа Kubernetes liveness probe.

    :return: JSON с общим статусом "alive".
    :rtype: JSONResponse
    """
    return JSONResponse(status_code=200, content={
        "status": "alive",
        "service": "core-app"
    })

@router.get("/ready", summary="Проверка готов ли сервер")
async def ready(session_factory: Callable[[], AsyncSession] = Depends(get_session_factory)) -> JSONResponse:
    """
    Readiness-check эндпоинт, подтверждающий, что все компоненты сервиса готовы к работе.

    Проверяет подключение к базе данных через SQL-запрос `SELECT 1`.

    :param session_factory: Зависимость, создающая сессию подключения к БД.
    :type session_factory: Callable[[], AsyncSession]
    :return: JSON с флагом готовности и статусами компонентов.
    :rtype: JSONResponse
    """
    components = {}

    async with session_factory() as session:
        await session.execute(text("SELECT 1"))
    components["database"] = "ready"

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "components": components,
            "service": "core-app"
        }
    )
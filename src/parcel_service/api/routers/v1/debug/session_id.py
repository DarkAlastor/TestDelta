from uuid import uuid4
from loguru import logger
from redis import Redis
from fastapi import APIRouter, Depends, HTTPException, Path

from src.parcel_service.api.deps.shared_deps import get_redis_session, build_session_cash_key

from src.parcel_service.api.schemas.error import ErrorResponse
from src.parcel_service.api.schemas.debug import SessionCreateResponse, SessionListResponse, SessionDetailResponse

router = APIRouter()

@router.get(
    path="/session",
    summary="Debug: Создать X-Session-Id",
    response_model=SessionCreateResponse,
    status_code=201,
    responses={
        201: {
            "model": SessionCreateResponse,
            "description": "Session create succuss"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal error"
        }
    }
)
async def debug_create_session_id(redis: Redis = Depends(get_redis_session)) -> SessionCreateResponse:
    """
    Создаёт новый X-Session-Id и сохраняет его в Redis на 30 минут.

    :param redis: Клиент Redis для хранения данных сессии.
    :type redis: Redis

    :return: Ответ с созданным session_id.
    :rtype: SessionCreateResponse
    """
    session_id = uuid4().hex
    cash_key = build_session_cash_key(session_id=session_id)

    await redis.set(name=cash_key, value="1", ex=1800)
    logger.debug(f"Successful session creation: {session_id}")
    return SessionCreateResponse(session_id=session_id)

@router.get(
    path="/session/all",
    summary="Debug: Получить все X-Session-Id",
    response_model=SessionListResponse,
    responses={
        200: {
            "model": SessionListResponse,
            "description": "Successful session retrieval "
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal error"
        }
    }
)
async def debug_get_all_sessions(redis: Redis = Depends(get_redis_session)) -> SessionListResponse:
    """
    Получает все сессии, хранящиеся в Redis.

    :param redis: Клиент Redis для хранения данных сессии.
    :type redis: Redis

    :return: Словарь всех найденных X-Session-Id и их значений.
    :rtype: SessionListResponse
    """
    cash_key = build_session_cash_key()
    keys = await redis.keys(cash_key)
    values = await redis.mget(*keys)
    logger.debug(f"Found keys: {keys}")
    result = dict(zip(keys, values))
    return SessionListResponse(sessions=result)

@router.get(
    "/session/{session_id}",
    summary="Debug: Получить конкретную X-Session-Id",
    response_model=SessionDetailResponse,
    responses={
        200: {
            "model": SessionDetailResponse,
            "description": "Successful session fetch"
        },
        404: {
            "model": ErrorResponse,
            "description": "Session not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    }
)
async def debug_get_session(session_id: str, redis: Redis = Depends(get_redis_session)) -> SessionDetailResponse:
    """
    Получает данные по конкретной X-Session-Id из Redis.

    :param session_id: Идентификатор сессии.
    :type session_id: str
    :param redis: Клиент Redis для хранения данных сессии.
    :type redis: Redis

    :raises HTTPException: Если сессия не найдена (404).

    :return: Данные по указанной сессии.
    :rtype: SessionDetailResponse
    """
    value = await redis.get(name=build_session_cash_key(session_id=session_id))
    if value is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetailResponse(session_id=session_id, data=value)
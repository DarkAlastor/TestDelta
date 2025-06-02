import json
from uuid import uuid4
from loguru import logger

from fastapi import APIRouter, Depends, Header
from redis import Redis

from src.parcel_service.api.deps.parcel_deps import get_uc_registry
from src.parcel_service.api.deps.shared_deps import get_redis_cash, get_uow, build_redis_cash_cash_key
from src.parcel_service.api.schemas.parcel import ParcelCreatedResponse, ParcelCreateSchema
from src.parcel_service.api.schemas.error import ErrorResponse
from src.parcel_service.domain.dto.dto_create_parcel import ParcelData, ParcelResult
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase

router = APIRouter()


@router.post(
    path="/",
    summary="Зарегистрировать посылку",
    response_model=ParcelCreatedResponse,
    responses={
        201: {"model": ParcelCreatedResponse, "description": "Parcel successfully registered"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def registry_parcel(
        parcel: ParcelCreateSchema,
        x_session_id: str = Header(...),
        uow: IUnitOfWork = Depends(get_uow),
        redis: Redis = Depends(get_redis_cash),
        use_case: IUseCase = Depends(get_uc_registry)
) -> ParcelCreatedResponse:
    """
    Регистрирует новую посылку для клиента.

    Создаёт уникальный parcel_id, сохраняет данные через UseCase, а затем кеширует входные данные
    в Redis на 5 минут (TTL 300 сек), используя ключ в формате parcel:<session_id>:<parcel_id>.

    :param parcel: Входные данные о посылке (имя, вес, тип, стоимость).
    :type parcel: ParcelCreateSchema
    :param x_session_id: Идентификатор сессии клиента (из заголовка запроса).
    :type x_session_id: str
    :param uow: Объект Unit of Work для транзакционного доступа к БД.
    :type uow: IUnitOfWork
    :param redis: Redis-клиент для кеширования.
    :type redis: Redis
    :param use_case: UseCase, реализующий бизнес-логику регистрации посылки.
    :type use_case: IUseCase
    :return: Ответ с parcel_id и сообщением об успехе.
    :rtype: ParcelCreatedResponse
    """

    # Генерация DTO
    dto_parcel = ParcelData(
        parcel_id=str(uuid4()),
        session_id=x_session_id,
        name=parcel.name,
        weight_kg=parcel.weight_kg,
        type_id=parcel.type_id,
        cost_adjustment_usd=parcel.cost_adjustment_usd
    )
    logger.info("Начало регистрации посылки | parcel_id={} session_id={}", dto_parcel.parcel_id, dto_parcel.session_id)

    # Вызов use case
    result: ParcelResult = await use_case(dto=dto_parcel, uow=uow, deps=None)

    # Кеширование DTO в Redis
    cache_key = build_redis_cash_cash_key("parcels", x_session_id, result.parcel_id)

    # Обрабатываем кеш
    try:
        if result:
            await redis.set(cache_key, json.dumps(dto_parcel.to_payload()), ex=60)
            logger.debug(f"[Redis] Set: {cache_key} -> {dto_parcel}")
    except Exception as e:
        logger.warning("Ошибка при установке кеша Redis | key={cache_key} | {error}", cache_key=cache_key, error=e)

    return ParcelCreatedResponse(parcel_id=result.parcel_id, message=result.message)


    # Индепотентность обеспечем в middelware так как нам нужно чтобы при ошибке не было дубликатов хоть
    # мы частично защетилиись но лучше обеспечивать такое через indepotency key !!!
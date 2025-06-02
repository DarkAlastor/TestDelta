import json
from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, Header, Query
from loguru import logger
from redis import Redis

from src.parcel_service.api.deps.parcel_deps import get_uc_parcels_for_id, get_uc_parcels_list_for_session_id, get_uc_parcels_all_types
from src.parcel_service.api.deps.shared_deps import get_redis_cash, get_uow, build_redis_cash_cash_key
from src.parcel_service.api.schemas.parcel import ParcelDetailResponse, ParcelListResponse
from src.parcel_service.api.schemas.parcel_types import ParcelTypeResponse
from src.parcel_service.domain.dto.dto_parcel_query import ParcelDetailQuery, ParcelDetailResult, ParcelQueryList
from src.parcel_service.domain.dto.dto_parcel_type import ParcelType
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase
from src.parcel_service.api.schemas.error import ErrorResponse

router = APIRouter()

@router.get(
    path="/all",
    summary="Получить список посылок пользователя",
    response_model=ParcelListResponse,
    responses={
        200: {"model": ParcelListResponse, "description": "Successful response"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal error"}
    }
)
async def get_all_parcels(
    x_session_id: str = Header(...),
    type_id: Optional[int] = Query(None),
    has_delivery_price: bool = Query(True),
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
    redis: Redis = Depends(get_redis_cash),
    uow: IUnitOfWork = Depends(get_uow),
    use_case: IUseCase = Depends(get_uc_parcels_list_for_session_id)
) -> ParcelListResponse:
    """
    Получение списка всех посылок, зарегистрированных в текущей сессии.

    Поддерживается фильтрация по типу посылки и по наличию рассчитанной стоимости доставки.
    Реализована пагинация: лимит и смещение (limit и offset).

    :param x_session_id: Идентификатор сессии пользователя, из заголовка запроса.
    :type x_session_id: str

    :param type_id: Фильтрация по ID типа посылки (опционально).
    :type type_id: Optional[int]

    :param has_delivery_price: Флаг фильтрации по наличию рассчитанной стоимости доставки.
    :type has_delivery_price: Optional[bool]

    :param limit: Количество посылок на странице (по умолчанию 20, минимум 1).
    :type limit: int

    :param offset: Смещение относительно начала выборки (по умолчанию 0).
    :type offset: int

    :param redis: Redis-клиент для кеша.
    :type redis: Redis

    :param uow: Объект UnitOfWork.
    :type uow: IUnitOfWork

    :param use_case: UseCase для получения списка посылок.
    :type use_case: IUseCase

    :returns: Список посылок пользователя с пагинацией.
    :rtype: ParcelListResponse

    :raises HTTPException 422: Ошибка валидации входных параметров.
    :raises HTTPException 500: Системная ошибка.
    """

    # смотрим в кеш если есть то сразу отдаем
    cache_key = f"parcels:{x_session_id}:offset={offset}:limit={limit}:type={type_id}:has_price={has_delivery_price}"

    cached = await redis.get(cache_key)
    logger.debug(f"[Redis] Get: {cache_key} -> {cached}")

    if cached:
        data = json.loads(cached)
        logger.debug(f"Найдено в кеше | key={cache_key} | data={data}: {data}")
        return ParcelListResponse(items=data["items"], total=data["total"])

    dto = ParcelQueryList(
        session_id=x_session_id,
        type_id=type_id,
        limit=limit,
        offset=offset,
        has_delivery_price=has_delivery_price
    )

    result: ParcelListResponse = await use_case(dto=dto, uow=uow, deps=None)
    logger.debug("result: {}", result)

    # Только первую страницу кешируем
    if offset == 0:
        items = []
        for item in result.items:
            delivery_price = (
                str(item.delivery_price_rub)
                if item.delivery_price_rub is not None
                else "Не рассчитано"
            )
            response_model = ParcelDetailResponse(
                parcel_id=item.parcel_id,
                name=item.name,
                weight_kg=item.weight_kg,
                type_id=item.type_id,
                cost_adjustment_usd=item.cost_adjustment_usd,
                delivery_price_rub=delivery_price
            )
            items.append(response_model.model_dump())

        to_cache = json.dumps({
            "items": items,
            "total": result.total
        })
        await redis.set(cache_key, to_cache, ex=300)  # Кеш 5 минута
        logger.debug(f"Кеш установлен : {cache_key} -> {to_cache}")

    return ParcelListResponse(
        items=[
            ParcelDetailResponse(
                parcel_id=item.parcel_id,
                name=item.name,
                weight_kg=item.weight_kg,
                type_id=item.type_id,
                cost_adjustment_usd=item.cost_adjustment_usd,
                delivery_price_rub=(
                    str(item.delivery_price_rub)
                    if item.delivery_price_rub is not None
                    else "Не рассчитано"
                )
            )
            for item in result.items
        ],
        total=result.total
    )

@router.get(
    path="/{parcel_id}",
    summary="Получить информацию о посылке",
    response_model=ParcelDetailResponse,
    responses={
        200: {"model": ParcelDetailResponse, "description": "Parcel information received successfully"},
        404: {"model": ErrorResponse, "description": "Parcel not found"},
        403: {"model": ErrorResponse, "description": "Access Denied"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },

)
async def get_parcel_detail(
    parcel_id: UUID,
    x_session_id: str = Header(...),
    uow: IUnitOfWork = Depends(get_uow),
    use_case: IUseCase = Depends(get_uc_parcels_for_id),
    redis: Redis = Depends(get_redis_cash)
) -> ParcelDetailResponse:
    """
    Возвращает детальную информацию о посылке по её идентификатору.

    Сначала выполняется попытка получения данных из Redis-кеша. Если данные найдены,
    они возвращаются напрямую без обращения к базе данных. Если данных в кеше нет —
    выполняется запрос к бизнес-логике и базе данных, результат сохраняется в Redis.

    :param parcel_id: Уникальный идентификатор посылки (UUID).
    :param x_session_id: Идентификатор сессии клиента (из заголовка запроса).
    :param uow: UnitOfWork для получения доступа к репозиториям.
    :param use_case: UseCase, обрабатывающий запрос получения данных о посылке.
    :param redis: Redis-клиент для кеширования.
    :return: Объект ParcelDetailResponse с полной информацией о посылке.
    :raises ParcelNotFoundError: Если посылка не найдена в базе данных.
    """

    # Сначала проверяем кеш
    cache_key = build_redis_cash_cash_key("parcels", x_session_id, str(parcel_id))

    cached = await redis.get(cache_key)
    logger.debug(f"Проверка кеша | key={cache_key}")

    if cached:
        try:
            data = json.loads(cached)
            logger.debug(f"Найдено в кеше | key={cache_key} | data={data}")
            return ParcelDetailResponse(
                parcel_id=data["parcel_id"],
                name=data["name"],
                weight_kg=data["weight_kg"],
                type_id=data["type_id"],
                cost_adjustment_usd=data["cost_adjustment_usd"],
                delivery_price_rub=str(data["delivery_price_rub"]) if data["delivery_price_rub"] is not None  else "Не рассчитано"
            )
        except Exception as e:
            logger.warning("Ошибка декодирования JSON из кеша | key={} | error={}", cache_key, str(e))
    logger.debug(f"Данные не найдены в кеше | key={cache_key}")

    # Потом идем в БД
    data_dto = ParcelDetailQuery(parcel_id=str(parcel_id), session_id=x_session_id)
    result: ParcelDetailResult = await use_case(dto=data_dto, uow=uow, deps=None)

    response = ParcelDetailResponse(
        parcel_id=result.parcel_id,
        name=result.name,
        weight_kg=result.weight_kg,
        type_id=result.type_id,
        cost_adjustment_usd=result.cost_adjustment_usd,
        delivery_price_rub=str(result.delivery_price_rub) if result.delivery_price_rub is not None else "Не рассчитано"
    )

    # Сохранение результат в кеш
    try:
        await redis.set(cache_key, response.model_dump_json(), ex=300)  # TTL = 5 минут
        logger.debug(f"Сохранено в кеш | key={cache_key}")
    except Exception as e:
        logger.warning("Ошибка при сохранении в Redis | key={} | error={}", cache_key, str(e))

    return response

@router.get(
    path="/parcels-types/",
    summary="Получить список типов посылок",
    response_model=List[ParcelTypeResponse],
    responses={
        200: {"model": List[ParcelTypeResponse], "description": "Parcel types information received successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },

)
async def get_parcel_types(
    uow: IUnitOfWork = Depends(get_uow),
    redis: Redis = Depends(get_redis_cash),
    use_case: IUseCase = Depends(get_uc_parcels_all_types)
) -> List[ParcelTypeResponse]:
    """
    Получение всех доступных типов посылок (одежда, электроника, разное).

    Типы хранятся в отдельной таблице в БД. Данные кешируются в Redis на 5 минут.

    :param uow: Объект UnitOfWork для доступа к данным.
    :type uow: IUnitOfWork

    :param redis: Redis-клиент для кеширования.
    :type redis: Redis

    :param use_case: UseCase, предоставляющий список типов.
    :type use_case: IUseCase

    :returns: Список типов посылок.
    :rtype: List[ParcelTypeResponse]

    :raises HTTPException 500: Ошибка при получении данных.
    """

    # Сначала проверяем кеш
    cache_key = build_redis_cash_cash_key("parcel_types","all")

    # Проверка кэша
    cached = await redis.get(cache_key)
    if cached:
        try:
            types_data = json.loads(cached)
            logger.debug(f"Найдено в кеше | key={cache_key} | types_data={types_data}")
            return [ParcelTypeResponse(**item) for item in types_data]
        except Exception as e:
            logger.warning("Ошибка декодирования JSON из кеша | key={} | error={}", cache_key, str(e))
    logger.debug(f"Данные не найдены в кеше | key={cache_key}")

    # Обращение к use case
    result: List[ParcelType] = await use_case(dto=None, uow=uow, deps=None)
    response = [ParcelTypeResponse(id=pt.id, name=pt.name) for pt in result]

    try:
        await redis.set(cache_key, json.dumps([r.model_dump() for r in response]), ex=300) # TTL = 5 минут
        logger.debug(f"Сохранено в кеш | key={cache_key}")
    except Exception as e:
        logger.warning("Ошибка при сохранении в Redis | key={} | error={}", cache_key, str(e))

    return response
from loguru import logger
from fastapi import APIRouter, Depends

from src.parcel_service.api.deps.debug_deps import get_uc_debug_recalculate
from src.parcel_service.api.deps.shared_deps import get_uow
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase
from src.parcel_service.api.schemas.debug import RecalculateResponse
from src.parcel_service.api.schemas.error import ErrorResponse
from src.parcel_service.domain.constants.events import EventType

router = APIRouter()

# тут нужен Rate limit если она внутреняя либо отключай
@router.get(
    path="/recalculate",
    summary="Debug: Пересчетать доставки",
    response_model=RecalculateResponse,
    responses={
        200: {
            "model": RecalculateResponse,
            "description": "Recalculation successfully started"
        },
        409: {
            "model": ErrorResponse,
            "description": "Recalculation event already exists or duplicate event ID"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    }
)
async def debug_recalculate(
        uow: IUnitOfWork = Depends(get_uow),
        use_case: IUseCase = Depends(get_uc_debug_recalculate)
) -> RecalculateResponse:
    """
    Выполняет отладочный пересчет стоимости доставки.

    :param uow: Абстракция для работы с базой данных и репозиториями.
    :type uow: IUnitOfWork
    :param use_case: Use case для пересчета стоимости доставки.
    :type use_case: IUseCase

    :return: Результат выполнения отладочного пересчета.
    :rtype: RecalculateResponse
    """

    await use_case(dto=None, uow=uow, deps=None)
    logger.info(f"Create event: {EventType.PARCEL_RECALCULATE}")
    return RecalculateResponse(message="Ok")
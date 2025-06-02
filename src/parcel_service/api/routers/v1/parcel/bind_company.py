from uuid import UUID
from loguru import logger
from fastapi import APIRouter, Depends

from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase
from src.parcel_service.domain.dto.dto_bind_company import BindCompanyData, BindCompanyResult

router = APIRouter()

from src.parcel_service.api.deps.shared_deps import get_uow
from src.parcel_service.api.deps.parcel_deps import get_uc_bind_compony
from src.parcel_service.api.schemas.error import ErrorResponse
from src.parcel_service.api.schemas.bind_company import BindCompany, BindCompanyResponse

@router.post(
    path="/{parcels_id}/bind-company",
    summary="Привязать компанию к посылке",
    response_model=BindCompanyResponse,
    responses={
        409: {"model": ErrorResponse, "description": "Already bound"},
        404: {"model": ErrorResponse, "description": "Company or Parcel not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
)
async def bind_company(
        parcels_id: UUID,
        bind_data:BindCompany,
        uow: IUnitOfWork = Depends(get_uow),
        use_case: IUseCase = Depends(get_uc_bind_compony)) -> BindCompanyResponse:
    """
    Привязывает посылку к транспортной компании, если она ещё не была привязана.

    Если посылка уже привязана — возвращается ошибка 409.

    :param parcels_id: Уникальный идентификатор посылки.
    :type parcels_id: UUID
    :param bind_data: Данные с ID компании, к которой требуется привязать посылку.
    :type bind_data: BindCompany
    :param uow: Unit of Work для работы с репозиториями и транзакциями.
    :type uow: IUnitOfWork
    :param use_case: Use case для привязки компании.
    :type use_case: IUseCase
    :return: Сообщение об успешной привязке.
    :rtype: BindCompanyResponse

    :raises HTTPException 409: Если посылка уже привязана к компании.
    """

    dto = BindCompanyData(parcel_id=str(parcels_id), company_id=bind_data.company_id)
    logger.info("Получен запрос на привязку посылки | parcel_id={} company_id={}", dto.parcel_id,dto. company_id)
    result: BindCompanyResult = await use_case(dto=dto, uow=uow, deps=None)

    logger.info("Привязка компании выполнена успешно | parcel_id={} company_id={}",dto.parcel_id,dto.company_id)
    return BindCompanyResponse(message=result.message)
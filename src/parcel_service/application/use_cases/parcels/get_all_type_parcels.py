from typing import List
from loguru import logger
from src.parcel_service.domain.interfaces.repository import IParcelTypeRepository
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase, TDeps
from src.parcel_service.domain.dto.dto_parcel_type import ParcelType


class GetAllTypeParcelsUseCase(IUseCase[None, List[ParcelType], None]):
    """
    UseCase для получения всех типов посылок.
    """

    async def __call__(self, dto: None, uow: IUnitOfWork, deps: TDeps = None) -> List[ParcelType]:
        try:
            async with uow:
                repo = await uow.get_repo(IParcelTypeRepository)
                logger.debug("Получение всех типов посылок из репозитория")

                types = await repo.list_all()

                if not types:
                    logger.warning("Типы посылок не найдены в базе данных")
                    return []

                logger.info("Типы посылок успешно получены | count={}", len(types))
                return [ParcelType(id=pt.id, name=pt.name) for pt in types]

        except Exception as e:
            logger.exception("Непредвиденная ошибка при получении типов посылок | {}", str(e))
            raise

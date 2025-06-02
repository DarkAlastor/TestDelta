from loguru import logger
from src.parcel_service.domain.dto.dto_parcel_query import ParcelDetailQuery, ParcelDetailResult
from src.parcel_service.domain.exceptions.domain_error import AccessDeniedError, ParcelNotFoundError
from src.parcel_service.domain.interfaces.repository import IOutboxEventRepository, IParcelRepository
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase, TDeps
from src.parcel_service.infrastructure.db.sql.models import OutboxEvent, Parcel


class GetParcelsForIdUseCase(IUseCase[ParcelDetailQuery, ParcelDetailResult, None]):
    """
    UseCase для получения информации о посылке по её ID.
    """

    async def __call__(self, dto: ParcelDetailQuery, uow: IUnitOfWork, deps: TDeps = None) -> ParcelDetailResult:
        try:
            async with uow:
                # Берем запись из таблице Parcel
                repo_parcel = await uow.get_repo(repo_type=IParcelRepository)
                parcel: Parcel = await repo_parcel.get_by_id(parcel_id=dto.parcel_id)

                if parcel:
                    logger.debug("Посылка найдена | parcel_id={}", parcel.id)
                    return ParcelDetailResult(
                        parcel_id=parcel.id,
                        name=parcel.name,
                        weight_kg=parcel.weight_kg,
                        type_id=parcel.type_id,
                        cost_adjustment_usd=parcel.cost_adjustment_usd,
                        delivery_price_rub=parcel.delivery_price_rub or "Not calculated"
                    )

                logger.debug("Посылка не найдена в основной таблице, ищем в Outbox | parcel_id={}", dto.parcel_id)
                repo_outbox = await uow.get_repo(IOutboxEventRepository)
                outbox_event: OutboxEvent | None = await repo_outbox.get_by_id(parcel_id=dto.parcel_id)

                if not outbox_event:
                    logger.warning("Посылка не найдена в Outbox | parcel_id={}", dto.parcel_id)
                    raise ParcelNotFoundError()

                if outbox_event.session_id != dto.session_id:
                    logger.warning("Доступ к посылке запрещён | parcel_id={} session_id={}", dto.parcel_id, dto.session_id)
                    raise AccessDeniedError()

                logger.debug("Посылка найдена в Outbox | parcel_id={} session_id={}", dto.parcel_id, dto.session_id)

                data = outbox_event.payload
                return ParcelDetailResult(
                    parcel_id=data["parcel_id"],
                    name=data["name"],
                    weight_kg=data["weight_kg"],
                    type_id=data["type_id"],
                    cost_adjustment_usd=data["cost_adjustment_usd"],
                    delivery_price_rub=data.get("delivery_price_rub", "Not calculated")
                )

        except ParcelNotFoundError as e:
            logger.warning("Поссылка не найдена | parcel_id={} | {}", dto.parcel_id, str(e))
            raise
        except AccessDeniedError as e:
            logger.warning("Доступ запрщен | parcel_id={} | {}", dto.parcel_id, str(e))
            raise
        except Exception as e:
            logger.exception("Непредвиденная ошибка при получении информации о посылке | parcel_id={} | {}", dto.parcel_id, str(e))
            raise


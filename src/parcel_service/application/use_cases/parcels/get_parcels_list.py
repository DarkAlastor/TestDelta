from loguru import logger
from src.parcel_service.domain.interfaces.uow import IUnitOfWork
from src.parcel_service.domain.interfaces.usecase import IUseCase, TDeps
from src.parcel_service.domain.interfaces.repository import IParcelCombinedRepository
from src.parcel_service.domain.dto.dto_parcel_query import ParcelQueryList, ParcelDetailQueryList, ParcelDetailResult


class GetParcelsListUseCase(IUseCase[ParcelQueryList, ParcelDetailQueryList, None]):
    """
    UseCase для получения списка посылок по session_id с возможностью фильтрации и пагинации.

    :param dto: Объект запроса, содержащий session_id, offset, limit, фильтры и пр.
    :param uow: Юнит работы, через который получаются репозитории.
    :param deps: Не используется в данном UseCase.
    :return: Список посылок и их общее количество в виде ParcelDetailQueryList.
    :raises Exception: При любых ошибках выполнения логируется и пробрасывается дальше.
    """

    async def __call__(self, dto: ParcelQueryList, uow: IUnitOfWork, deps: TDeps = None) -> ParcelDetailQueryList:
        try:
            async with uow:
                repo_combine = await uow.get_repo(IParcelCombinedRepository)
                logger.debug("Получен репозиторий ParcelCombinedRepository")

                # Получаем ID + source по пагинации
                ids_with_source = await repo_combine.list_paginated(
                    session_id=dto.session_id,
                    limit=dto.limit,
                    offset=dto.offset,
                    type_id=dto.type_id
                )
                logger.info("Получено %s ID из пагинации", len(ids_with_source))

                # Получаем общее количество уникальных записей с учётом фильтра
                total = await repo_combine.count(
                    session_id=dto.session_id,
                    has_delivery_price=dto.has_delivery_price,
                    type_id=dto.type_id
                )
                logger.info("Общее количество подходящих записей: %s", total)

                # Разделяем ID по источникам
                parcel_ids = [pid for pid, src in ids_with_source if src == "parcel"]
                outbox_ids = [pid for pid, src in ids_with_source if src == "outbox"]

                # Получаем записи
                parcels = await repo_combine.get_parcels_by_ids(parcel_ids)
                outboxes = await repo_combine.get_outbox_by_parcel_ids(outbox_ids)

                # Преобразуем в DTO
                parcel_map = {
                    p.id: ParcelDetailResult(
                        parcel_id=p.id,
                        name=p.name,
                        weight_kg=p.weight_kg,
                        type_id=p.type_id,
                        cost_adjustment_usd=p.cost_adjustment_usd,
                        delivery_price_rub=(
                            p.delivery_price_rub if p.delivery_price_rub is not None
                            else ("Не рассчитано" if not dto.has_delivery_price else None)
                        )
                    )
                    for p in parcels
                    if not dto.has_delivery_price or p.delivery_price_rub is not None
                }

                outbox_map = {
                    o.parcel_id: ParcelDetailResult(
                        parcel_id=o.parcel_id,
                        name=o.payload.get("name"),
                        weight_kg=float(o.payload.get("weight_kg", 0.0)),
                        type_id=o.payload.get("type_id"),
                        cost_adjustment_usd=o.payload.get("cost_adjustment_usd"),
                        delivery_price_rub=(
                            o.payload.get("delivery_price_rub")
                            if o.payload.get("delivery_price_rub") is not None
                            else ("Не рассчитано" if not dto.has_delivery_price else None)
                        )
                    )
                    for o in outboxes
                    if not dto.has_delivery_price or o.payload.get("delivery_price_rub") is not None
                }

                # Объединяем и возвращаем
                result_map = {**parcel_map, **outbox_map}
                ordered_results = [
                    result_map[pid] for pid, _ in ids_with_source if pid in result_map
                ]
                logger.debug("result_map: {}", result_map)

                return ParcelDetailQueryList(items=ordered_results, total=total)
        except Exception as e:
            # Можно логировать здесь
            logger.exception("Не удалось получить список посылок: %s", str(e))
            raise


from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, literal, union_all, func, desc

from .registry import RepositoryRegistry
from src.parcel_service.domain.interfaces.repository import IParcelCombinedRepository
from src.parcel_service.infrastructure.db.sql.models import Parcel, OutboxEvent


@RepositoryRegistry.register(IParcelCombinedRepository)
class ParcelCombinedRepository(IParcelCombinedRepository):
    """
    Агрегирующий репозиторий для получения комбинированной информации о посылках
    и связанных outbox-событиях.

    Используется для:
    - получения актуального списка посылок, включая неподтверждённые события;
    - фильтрации, пагинации, подсчёта количества;
    - объединения информации из таблиц `parcels` и `outbox_events`.

    :param session: Асинхронная SQLAlchemy-сессия.
    :type session: AsyncSession
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def _log_identity_debug(self) -> int:
        """
        Отладочный метод: возвращает уникальный ID текущего экземпляра.

        :return: Идентификатор экземпляра.
        :rtype: int
        """
        return id(self)

    def _json_extract_expr(self) -> str:
        """
        Возвращает корректное выражение SQL для извлечения `parcel_id` из JSON `payload`
        в зависимости от используемого диалекта (SQLite, MySQL).

        :raises NotImplementedError: Если диалект не поддерживается.
        :return: SQL-выражение для извлечения parcel_id из JSON.
        :rtype: str
        """

        dialect = self._session.bind.dialect.name
        if dialect == "sqlite":
            return "json_extract(payload, '$.parcel_id')"
        elif dialect == "mysql":
            return "JSON_UNQUOTE(JSON_EXTRACT(payload, '$.parcel_id'))"
        else:
            raise NotImplementedError(f"Unsupported DB dialect: {dialect}")

    async def get_parcels_by_ids(self, ids: List[str]) -> List[Parcel]:
        """
        Получает список посылок по их идентификаторам.

        :param ids: Список parcel_id.
        :type ids: List[str]
        :return: Список объектов Parcel.
        :rtype: List[Parcel]
        """
        if not ids:
            return []
        stmt = select(Parcel).where(Parcel.id.in_(ids))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_outbox_by_parcel_ids(self, ids: List[str]) -> List[OutboxEvent]:
        """
        Получает список OutboxEvent по `parcel_id`.

        :param ids: Список parcel_id.
        :type ids: List[str]
        :return: Список объектов OutboxEvent.
        :rtype: List[OutboxEvent]
        """
        if not ids:
            return []
        stmt = select(OutboxEvent).where(OutboxEvent.parcel_id.in_(ids))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count(
            self,
            session_id: str,
            has_delivery_price: bool = False,
            type_id: Optional[int] = None
    ) -> int:

        """
        Подсчитывает количество уникальных parcel_id (из таблиц `parcels` и `outbox_events`),
        соответствующих фильтру по session_id, типу и флагу наличия цены доставки.

        :param session_id: Идентификатор пользовательской сессии.
        :param has_delivery_price: Если True — учитываются только записи с ненулевой delivery_price_rub.
        :param type_id: Фильтрация по типу посылки.
        :return: Количество подходящих parcel_id.
        :rtype: int
        """
        parcels_query = select(
            Parcel.id.label("parcel_id"),
            Parcel.delivery_price_rub.label("delivery_price_rub"),
            Parcel.type_id.label("type_id"),
            literal("parcel").label("source")
        ).where(Parcel.session_id == session_id)

        if type_id is not None:
            parcels_query = parcels_query.where(Parcel.type_id == type_id)

        outbox_query = select(
            OutboxEvent.payload["parcel_id"].as_string().label("parcel_id"),
            OutboxEvent.payload["delivery_price_rub"].as_float().label("delivery_price_rub"),
            OutboxEvent.payload["type_id"].as_integer().label("type_id"),
            literal("outbox").label("source")
        ).where(
            OutboxEvent.session_id == session_id,
            OutboxEvent.event_type == "registry_parcel",
            OutboxEvent.applied == False
        )

        if type_id is not None:
            outbox_query = outbox_query.where(
                OutboxEvent.payload["type_id"].as_integer() == type_id
            )

        unified = union_all(parcels_query, outbox_query).subquery("unified")

        ranked = select(
            unified.c.parcel_id,
            unified.c.delivery_price_rub,
            func.row_number()
            .over(partition_by=unified.c.parcel_id,
                  order_by=desc(unified.c.source == "parcel"))
            .label("rn")
        ).subquery("ranked")

        stmt = select(func.count()).where(ranked.c.rn == 1)

        if has_delivery_price:
            stmt = stmt.where(ranked.c.delivery_price_rub.isnot(None))

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_paginated(
            self,
            session_id: str,
            limit: int,
            offset: int,
            type_id: Optional[int] = None
    ) -> List[Tuple[str, str]]:
        """
        Возвращает постраничный список parcel_id и source ("parcel" или "outbox"),
        отфильтрованный по session_id и type_id.

        Объединяет данные из таблиц `parcels` и `outbox_events`,
        удаляя дубликаты с приоритетом записей из `parcels`.

        :param session_id: Идентификатор пользовательской сессии.
        :param limit: Лимит записей.
        :param offset: Смещение.
        :param type_id: Фильтр по типу посылки.
        :return: Список кортежей (parcel_id, source).
        :rtype: List[Tuple[str, str]]
        """
        parcels_query = select(
            Parcel.id.label("parcel_id"),
            Parcel.created_at.label("created_at"),
            Parcel.type_id.label("type_id"),
            literal("parcel").label("source")
        ).where(Parcel.session_id == session_id)

        if type_id is not None:
            parcels_query = parcels_query.where(Parcel.type_id == type_id)

        outbox_query = select(
            OutboxEvent.payload["parcel_id"].as_string().label("parcel_id"),
            OutboxEvent.created_at.label("created_at"),
            OutboxEvent.payload["type_id"].as_integer().label("type_id"),
            literal("outbox").label("source")
        ).where(
            OutboxEvent.session_id == session_id,
            OutboxEvent.event_type == "registry_parcel",
            OutboxEvent.applied == False
        )

        if type_id is not None:
            outbox_query = outbox_query.where(OutboxEvent.payload["type_id"].as_integer() == type_id)

        unified_query = union_all(parcels_query, outbox_query).subquery("unified")

        ranked = select(
            unified_query.c.parcel_id,
            unified_query.c.source,
            func.row_number()
            .over(partition_by=unified_query.c.parcel_id,
                  order_by=desc(unified_query.c.source == "parcel"))
            .label("rn")
        ).subquery("ranked")

        final_stmt = (
            select(ranked.c.parcel_id, ranked.c.source)
            .where(ranked.c.rn == 1)
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(final_stmt)
        return [(row.parcel_id, row.source) for row in result.all()]

    # async def count(self, session_id: str, has_delivery_price: bool = False) -> int:
    #     """
    #     Подсчитывает количество уникальных parcel_id, либо только с рассчитанной стоимостью доставки.
    #
    #     :param session_id: Идентификатор сессии пользователя.
    #     :type session_id: str
    #     :param has_delivery_price: Флаг фильтрации только посылок с рассчитанной delivery_price.
    #     :type has_delivery_price: bool
    #     :return: Количество посылок, удовлетворяющих условиям.
    #     :rtype: int
    #     """
    #     json_expr = self._json_extract_expr()
    #     condition = "WHERE rn = 1"
    #     if has_delivery_price:
    #         # Добавим условие фильтрации по delivery_price
    #         condition += " AND delivery_price_rub IS NOT NULL"
    #
    #     stmt = text(f"""
    #         SELECT COUNT(*) FROM (
    #             SELECT parcel_id, delivery_price_rub FROM (
    #                 SELECT *,
    #                        ROW_NUMBER() OVER (
    #                            PARTITION BY parcel_id
    #                            ORDER BY source = 'parcel' DESC, created_at DESC
    #                        ) as rn
    #                 FROM (
    #                     SELECT id AS parcel_id, created_at, 'parcel' AS source, delivery_price_rub
    #                     FROM parcels
    #                     WHERE session_id = :session_id
    #                     AND (
    #                       :type_id IS NULL OR
    #                       JSON_EXTRACT(payload, '$.type_id') = :type_id
    #                     )
    #                     UNION ALL
    #
    #                     SELECT {json_expr} AS parcel_id, created_at, 'outbox' AS source,
    #                            json_extract(payload, '$.delivery_price_rub') AS delivery_price_rub
    #                     FROM outbox_events
    #                     WHERE session_id = :session_id
    #                       AND event_type = 'registry_parcel'
    #                       AND applied = false
    #                 ) unified
    #             ) filtered
    #             {condition}
    #         ) final
    #     """).bindparams(session_id=session_id)
    #
    #     result = await self._session.execute(stmt)
    #     return result.scalar_one()

    # async def list_paginated(self, session_id: str, limit: int, offset: int, type_id:Optional[int]=None) -> List[Tuple[str, str]]:
    #     """
    #      Возвращает постраничный список актуальных посылок (Parcel или Outbox),
    #      сгруппированных по `parcel_id` с приоритетом `Parcel > Outbox`.
    #
    #      :param session_id: Идентификатор пользовательской сессии.
    #      :type session_id: str
    #      :param limit: Количество записей на странице.
    #      :type limit: int
    #      :param offset: Смещение (offset) от начала списка.
    #      :type offset: int
    #      :param type_id: Необязательный фильтр по типу посылки.
    #      :type type_id: Optional[int]
    #      :return: Список кортежей (parcel_id, source), где source = 'parcel' или 'outbox'.
    #      :rtype: List[Tuple[str, str]]
    #      """
    #     json_expr = self._json_extract_expr()
    #     stmt = text(f"""
    #         SELECT parcel_id, created_at, source FROM (
    #             SELECT *,
    #                    ROW_NUMBER() OVER (
    #                        PARTITION BY parcel_id
    #                        ORDER BY
    #                            source = 'parcel' DESC,
    #                            created_at DESC
    #                    ) as rn
    #             FROM (
    #                 SELECT id AS parcel_id, created_at, 'parcel' AS source
    #                 FROM parcels
    #                 WHERE session_id = :session_id
    #                 AND (:type_id IS NULL OR type_id = :type_id)
    #
    #                 UNION ALL
    #
    #                 SELECT {json_expr} AS parcel_id, created_at, 'outbox' AS source
    #                 FROM outbox_events
    #                 WHERE session_id = :session_id
    #                   AND event_type = 'registry_parcel'
    #                   AND applied = false
    #             ) unified
    #         ) filtered
    #         WHERE rn = 1
    #         ORDER BY parcel_id
    #         LIMIT :limit OFFSET :offset
    #     """).bindparams(
    #         session_id=session_id,
    #         type_id=type_id,
    #         limit=limit,
    #         offset=offset
    #     )
    #
    #     result = await self._session.execute(stmt)
    #     return [(row[0], row[2]) for row in result.all()]
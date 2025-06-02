import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Базовая модель со стандартными полями:
    """
    pass

class Parcel(Base):
    """
    Модель посылки.

    :ivar id: Уникальный идентификатор посылки (UUID).
    :ivar session_id: Идентификатор пользовательской сессии.
    :ivar name: Название посылки.
    :ivar weight_kg: Вес в килограммах.
    :ivar type_id: Ссылка на тип посылки.
    :ivar cost_adjustment_usd: Стоимость содержимого в долларах.
    :ivar delivery_price_rub: Рассчитанная стоимость доставки в рублях.
    :ivar company_id: Ссылка на транспортную компанию (если установлена).
    :ivar created_at: Дата создания записи.
    :ivar updated_at: Дата последнего изменения.
    :ivar parcel_type: Объект типа посылки (связь many-to-one).
    :ivar company: Объект компании (связь many-to-one).

    :constraint uq_parcels_name_session: Уникальность сочетания name + session_id.
    :index ix_parcels_session_type: Индекс по session_id и type_id.
    :index ix_parcels_session_created: Индекс по session_id и created_at.
    """
    __tablename__ = "parcels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    type_id: Mapped[int] = mapped_column(nullable=False, index=True)
    cost_adjustment_usd: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_price_rub: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True, default=None)
    company_id: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc))



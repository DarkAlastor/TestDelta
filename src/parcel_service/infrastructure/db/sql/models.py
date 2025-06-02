import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import UniqueConstraint

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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
    type_id: Mapped[int] = mapped_column(ForeignKey("parcel_types.id"), nullable=False, index=True)
    cost_adjustment_usd: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_price_rub: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True, default=None)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("name", "session_id", name="uq_parcels_name_session"),
        Index("ix_parcels_session_type", "session_id", "type_id"),
        Index("ix_parcels_session_created", "session_id", "created_at"),
    )

    parcel_type = relationship("ParcelType")
    company = relationship("Company")

class ParcelType(Base):
    """
    Модель справочника типов посылок.

    :ivar id: Уникальный идентификатор типа.
    :ivar name: Название типа (например, "одежда", "электроника").
    """
    __tablename__ = "parcel_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

class Company(Base):
    """
    Модель транспортной компании.

    :ivar id: Уникальный идентификатор компании.
    :ivar name: Название компании.
    :ivar description: Описание или дополнительная информация.
    :ivar created_at: Дата регистрации компании в системе.
    """
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc), nullable=True)

class OutboxEvent(Base):
    """
    Модель Outbox-события (реализация паттерна Outbox для надёжной публикации событий).

    :ivar id: Уникальный идентификатор события.
    :ivar parcel_id: Связанная посылка (если применимо).
    :ivar session_id: Идентификатор сессии инициатора.
    :ivar event_type: Тип события (например, "parcel.registered").
    :ivar payload: Полезная нагрузка события (в формате JSON).
    :ivar applied: Было ли событие уже обработано.
    :ivar created_at: Дата создания события.
    :ivar published_at: Дата публикации события во внешний брокер (если применимо).
    """
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, nullable=False)
    parcel_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

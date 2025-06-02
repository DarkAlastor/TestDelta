from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """
    Базовая модель со стандартными полями:
    """
    pass

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

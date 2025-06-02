# conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
from src.parcel_service.infrastructure.db.sql.models import Base, Parcel, OutboxEvent


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def filled_db_session(db_session):
    session_id = "test-session"

    # Только в Parcel
    parcels = [
        Parcel(
            id=f"p{i}",
            session_id=session_id,
            name=f"Parcel {i}",
            weight_kg=1.0 + i,
            type_id=i,
            cost_adjustment_usd=0.5 * i,
            delivery_price_rub=None if i in [2, 5] else 100 + i * 10,  # p2 и p5 -> None
            company_id=None,
            created_at=datetime(2024, 1, 1 + i, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1 + i, tzinfo=timezone.utc),
        ) for i in range(1, 7)
    ]

    # Только в Outbox
    outboxes = [
        OutboxEvent(
            id=f"e{i}",
            parcel_id=f"o{i}",
            session_id=session_id,
            event_type="registry_parcel",
            applied=False,
            created_at=datetime(2024, 1, 10 + i, tzinfo=timezone.utc),
            payload={
                "parcel_id": f"o{i}",
                "name": f"Outbox {i}",
                "weight_kg": 2.0 + i,
                "type_id": i,
                "cost_adjustment_usd": 1.0,
                "delivery_price_rub": None if i == 4 else 200 + i * 10,  # o4 -> None
            }
        ) for i in range(1, 7)
    ]

    # Один и тот же ID в обеих таблицах
    duplicate_id = "shared-id"
    parcel_dupe = Parcel(
        id=duplicate_id,
        session_id=session_id,
        name="Parcel Shared",
        weight_kg=9.9,
        type_id=9,
        cost_adjustment_usd=5.0,
        delivery_price_rub=None,  # специально None
        company_id=None,
        created_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
    )

    outbox_dupe = OutboxEvent(
        id="e-shared",
        parcel_id=duplicate_id,
        session_id=session_id,
        event_type="registry_parcel",
        applied=False,
        created_at=datetime(2024, 2, 2, tzinfo=timezone.utc),
        payload={
            "parcel_id": duplicate_id,
            "name": "Outbox Shared",
            "weight_kg": 9.8,
            "type_id": 99,
            "cost_adjustment_usd": 9.9,
            "delivery_price_rub": None,  # тоже None
        }
    )

    db_session.add_all(parcels + outboxes + [parcel_dupe, outbox_dupe])
    await db_session.commit()
    return db_session, session_id


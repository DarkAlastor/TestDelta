import pytest
from src.parcel_service.infrastructure.repository.parcel_combain import ParcelCombinedRepository
from src.parcel_service.application.use_cases.parcels.get_parcels_list import GetParcelsListUseCase
from src.parcel_service.domain.dto.dto_parcel_query import ParcelQueryList


class DummyUoW:
    def __init__(self, repo):
        self.repo = repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get_repo(self, repo_type):
        return self.repo


@pytest.mark.anyio
async def test_no_duplicates_when_id_in_both_tables(filled_db_session):
    """Проверяем, что ID присутствующий в обеих таблицах возвращается один раз"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)

    dto = ParcelQueryList(session_id=session_id, limit=100, offset=0, type_id=None)
    usecase = GetParcelsListUseCase()
    result = await usecase(dto, uow)

    all_ids = [item.parcel_id for item in result.items]
    assert all_ids.count("shared-id") == 1
    assert result.total == 13
    assert len(result.items) == 13


@pytest.mark.anyio
async def test_pagination_partial_page_verbose(filled_db_session):
    """Проверяем пагинацию — 3 записи с offset=2"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)
    usecase = GetParcelsListUseCase()

    dto = ParcelQueryList(session_id=session_id, limit=3, offset=2, type_id=None)
    result = await usecase(dto, uow)

    assert result.total == 13
    assert len(result.items) == 3
    assert len(set(item.parcel_id for item in result.items)) == 3


@pytest.mark.anyio
async def test_pagination_full_page_and_empty_offset(filled_db_session):
    """Проверка второй страницы и пустой страницы за пределами total"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)
    usecase = GetParcelsListUseCase()

    # Страница 2
    dto = ParcelQueryList(session_id=session_id, limit=5, offset=5, type_id=None)
    result = await usecase(dto, uow)
    assert result.total == 13
    assert len(result.items) == 5

    # Offset за пределами
    dto = ParcelQueryList(session_id=session_id, limit=5, offset=20, type_id=None)
    result = await usecase(dto, uow)
    assert result.total == 13
    assert len(result.items) == 0


@pytest.mark.anyio
async def test_only_with_delivery_price(filled_db_session):
    """Проверка фильтрации по флагу has_delivery_price=True"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)

    dto = ParcelQueryList(session_id=session_id, limit=100, offset=0, has_delivery_price=True, type_id=None)
    usecase = GetParcelsListUseCase()
    result = await usecase(dto, uow)

    # Все значения должны быть НЕ None и НЕ строкой "No calculated"
    assert all(
        item.delivery_price_rub is not None and item.delivery_price_rub != "No calculated"
        for item in result.items
    )
    assert result.total == len(result.items)
    assert result.total == 9  # 13 - 4 с None


@pytest.mark.anyio
async def test_replace_none_with_label(filled_db_session):
    """Проверка замены delivery_price_rub=None на строку "No calculated"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)

    # Вручную занулим одно значение
    parcel = (await repo.get_parcels_by_ids(["p1"]))[0]
    parcel.delivery_price_rub = None
    await db_session.commit()

    dto = ParcelQueryList(session_id=session_id, limit=100, offset=0, has_delivery_price=False, type_id=None)
    usecase = GetParcelsListUseCase()
    result = await usecase(dto, uow)

    # Ищем p1
    p1 = next((item for item in result.items if item.parcel_id == "p1"), None)
    assert p1 is not None
    assert p1.delivery_price_rub == "Не рассчитано"

@pytest.mark.anyio
async def test_filter_by_type_id_in_parcel_only(filled_db_session):
    """Фильтрация по type_id=3: данные есть и в Parcel, и в Outbox"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)

    dto = ParcelQueryList(session_id=session_id, limit=100, offset=0, type_id=3)
    usecase = GetParcelsListUseCase()
    result = await usecase(dto, uow)

    ids = [item.parcel_id for item in result.items]
    assert set(ids) == {"p3", "o3"}  # потому что оба существуют и не дублируются по ID
    assert result.total == 2


@pytest.mark.anyio
async def test_filter_by_type_id_in_outbox_only(filled_db_session):
    """Фильтрация по type_id=6: есть и в Outbox, и в Parcel"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)

    dto = ParcelQueryList(session_id=session_id, limit=100, offset=0, type_id=6)
    usecase = GetParcelsListUseCase()
    result = await usecase(dto, uow)

    ids = [item.parcel_id for item in result.items]
    assert set(ids) == {"p6", "o6"}
    assert result.total == 2


@pytest.mark.anyio
async def test_filter_by_type_id_no_match(filled_db_session):
    """Фильтрация по несуществующему type_id"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)

    dto = ParcelQueryList(session_id=session_id, limit=100, offset=0, type_id=999)
    usecase = GetParcelsListUseCase()
    result = await usecase(dto, uow)

    assert result.total == 0
    assert len(result.items) == 0


@pytest.mark.anyio
async def test_filter_by_type_id_prefers_parcel_over_outbox(filled_db_session):
    """Если ID есть и в Parcel и в Outbox — используется Parcel"""
    db_session, session_id = filled_db_session
    repo = ParcelCombinedRepository(db_session)
    uow = DummyUoW(repo)

    dto = ParcelQueryList(session_id=session_id, limit=100, offset=0, type_id=9)
    usecase = GetParcelsListUseCase()
    result = await usecase(dto, uow)

    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].parcel_id == "shared-id"
    assert result.items[0].type_id == 9






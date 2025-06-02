from typing import Optional
from bson.son import SON
from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

from src.parcel_service.api.deps.shared_deps import get_mongo_db
from src.parcel_service.api.schemas.error import ErrorResponse
from src.parcel_service.api.schemas.analytics import AnalyticsResponse, DeliveryCostItem


@router.get(
    "/delivery/summary",
    response_model=AnalyticsResponse,
    summary="Сумма доставок по типам за день",
    responses={
        200: {"model": AnalyticsResponse, "description": "Successful"},
        400: {"model": ErrorResponse, "description": "Error date validation"},
        500: {"model": ErrorResponse, "description": "Internal server error"}

    }
)
async def get_delivery_summary(
        date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
        mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)
) -> AnalyticsResponse:
    """
    Возвращает сумму стоимости доставок по типам за указанную дату (или за текущую дату по умолчанию).

    :param date: Дата в формате YYYY-MM-DD (опционально). Если не указана — используется текущий день (UTC).
    :type date: Optional[str]

    :param mongo_db: Клиент MongoDB (через Depends).
    :type mongo_db: AsyncIOMotorDatabase

    :return: Объект с датой, типом агрегации и списком агрегированных значений.
    :rtype: AnalyticsResponse

    :raises HTTPException 400: В случае некорректного формата даты.
    """
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d") if date else datetime.utcnow()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    start = datetime(date_obj.year, date_obj.month, date_obj.day)
    end = start + timedelta(days=1)

    pipeline = [
        {"$match": {"calculated_at": {"$gte": start, "$lt": end}}},
        {"$group": {
            "_id": "$type_id",  # Предполагаем, что name хранится в Mongo (иначе нужно join/lookup)
            "total": {"$sum": "$calculated_price"}
        }},
        {"$sort": SON([("_id", 1)])}
    ]

    cursor = mongo_db["calculations"].aggregate(pipeline)
    items = []

    async for doc in cursor:
        items.append(DeliveryCostItem(type=doc["_id"], total=round(doc["total"], 2)))

    return AnalyticsResponse(
        date=start,
        group_by="type",
        items=items
    )
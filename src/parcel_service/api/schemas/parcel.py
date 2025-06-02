import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, conint

class ParcelCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Название посылки")
    weight_kg: float = Field(0.01, ge=0.01, le=100.0, description="Вес в килограммах (от 0.01 до 100)")
    type_id: conint(ge=1, le=3) = Field(1, description="ID типа посылки (1-одежда, 2-электроника, 3-другое)")
    cost_adjustment_usd: float = Field(0.1, ge=0.1, le=1_000_000.0, description="Стоимость содержимого в $")

    @classmethod
    @field_validator("name", mode='before')
    def name_must_be_clean(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не может быть пустым")

        if not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\- ]+$", value):
            raise ValueError("Только буквы, цифры, пробелы и дефисы допустимы")

        if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise ValueError("Недопустимые символы управления")

        if re.search(r"(.)\1{5,}", value):
            raise ValueError("Слишком много повторяющихся символов")

        return value

    class Config:
        extra = "forbid"

class ParcelCreatedResponse(BaseModel):
    parcel_id: str
    message: str

class ParcelDetailResponse(BaseModel):
    parcel_id: str
    name: str
    weight_kg: float
    type_id: int
    cost_adjustment_usd: float
    delivery_price_rub: Optional[float | str]

class ParcelListResponse(BaseModel):
    items: List[ParcelDetailResponse]
    total: int

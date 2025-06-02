from pydantic import BaseModel
from typing import Dict

class SessionCreateResponse(BaseModel):
    session_id: str

class SessionListResponse(BaseModel):
    sessions: Dict[str, str]

class SessionDetailResponse(BaseModel):
    session_id: str
    data: str

class RecalculateResponse(BaseModel):
    message: str
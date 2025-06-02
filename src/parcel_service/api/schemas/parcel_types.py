from pydantic import BaseModel

class ParcelTypeResponse(BaseModel):
    id: int
    name: str

from pydantic import BaseModel, Field

class BindCompany(BaseModel):
    company_id: int = Field(ge=1, description="ID of the transport company (must be ≥ 1)")

class BindCompanyResponse(BaseModel):
    message: str
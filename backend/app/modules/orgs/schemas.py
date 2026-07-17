from datetime import datetime

from pydantic import BaseModel


class OrganizationOut(BaseModel):
    id: int
    name: str
    tier: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationUpdate(BaseModel):
    name: str | None = None
    tier: str | None = None

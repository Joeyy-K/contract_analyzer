from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ContractBase(BaseModel):
    filename: str
    file_type: str


class ContractCreate(ContractBase):
    content: str
    user_id: int


class ContractInDB(ContractBase):
    id: int
    user_id: int
    content: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class Contract(ContractInDB):
    pass


class ContractResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
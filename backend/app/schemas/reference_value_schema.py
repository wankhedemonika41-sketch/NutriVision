from pydantic import BaseModel
from typing import Optional


class ReferenceValueCreate(BaseModel):
    nutrient: str
    reference_value: float
    unit: str
    basis: str
    description: Optional[str] = None


class ReferenceValueResponse(BaseModel):
    id: int
    nutrient: str
    reference_value: float
    unit: str
    basis: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
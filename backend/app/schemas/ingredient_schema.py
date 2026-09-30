from pydantic import BaseModel
from typing import Optional


class IngredientCreate(BaseModel):
    product_id: int
    name: str
    category: Optional[str] = None
    explanation: Optional[str] = None


class IngredientResponse(BaseModel):
    id: int
    product_id: int
    name: str
    category: Optional[str] = None
    explanation: Optional[str] = None

    class Config:
        from_attributes = True
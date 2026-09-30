from pydantic import BaseModel
from typing import Optional


class NutritionCreate(BaseModel):
    product_id: int

    calories: Optional[float] = None
    sugar: Optional[float] = None
    total_fat: Optional[float] = None
    saturated_fat: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None
    sodium: Optional[float] = None
    fiber: Optional[float] = None


class NutritionResponse(BaseModel):
    id: int
    product_id: int

    calories: Optional[float] = None
    sugar: Optional[float] = None
    total_fat: Optional[float] = None
    saturated_fat: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None
    sodium: Optional[float] = None
    fiber: Optional[float] = None

    class Config:
        from_attributes = True
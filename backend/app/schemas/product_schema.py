from pydantic import BaseModel
from typing import Optional


# ============================================================
# PRODUCT CREATE
# ============================================================

class ProductCreate(BaseModel):

    product_name: str

    brand: Optional[str] = None

    category: Optional[str] = None

    sub_category: Optional[str] = None

    barcode: Optional[str] = None

    serving_size: Optional[str] = None

    ingredients: Optional[str] = None

    price_inr: Optional[float] = None

    source_of_data: Optional[str] = None

    collection_date: Optional[str] = None

    collected_by: Optional[str] = None

    remarks: Optional[str] = None


# ============================================================
# PRODUCT RESPONSE
# ============================================================

class ProductResponse(BaseModel):

    id: int

    product_name: str

    brand: Optional[str] = None

    category: Optional[str] = None

    sub_category: Optional[str] = None

    barcode: Optional[str] = None

    serving_size: Optional[str] = None

    ingredients: Optional[str] = None

    price_inr: Optional[float] = None

    source_of_data: Optional[str] = None

    collection_date: Optional[str] = None

    collected_by: Optional[str] = None

    remarks: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# NUTRITION DETAILS
# ============================================================

class NutritionDetails(BaseModel):

    calories: Optional[float] = None

    carbohydrates: Optional[float] = None

    protein: Optional[float] = None

    total_fat: Optional[float] = None

    saturated_fat: Optional[float] = None

    trans_fat: Optional[float] = None

    sugar: Optional[float] = None

    sodium: Optional[float] = None

    fiber: Optional[float] = None

    cholesterol: Optional[float] = None

    calcium: Optional[float] = None

    vitamin: Optional[str] = None

    iron: Optional[float] = None

    class Config:
        from_attributes = True


# ============================================================
# PRODUCT DETAILS RESPONSE
# ============================================================

class ProductDetailsResponse(BaseModel):

    product: ProductResponse

    nutrition: Optional[NutritionDetails] = None
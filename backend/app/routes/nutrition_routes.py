from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.nutrition import Nutrition
from app.models.product import Product
from app.schemas.nutrition_schema import (
    NutritionCreate,
    NutritionResponse
)


router = APIRouter(
    prefix="/nutrition",
    tags=["Nutrition"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=NutritionResponse)
def create_nutrition(
    nutrition: NutritionCreate,
    db: Session = Depends(get_db)
):

    # Check whether product exists
    product = db.query(Product).filter(
        Product.id == nutrition.product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check whether nutrition already exists
    existing_nutrition = db.query(Nutrition).filter(
        Nutrition.product_id == nutrition.product_id
    ).first()

    if existing_nutrition:
        raise HTTPException(
            status_code=400,
            detail="Nutrition data already exists for this product"
        )

    new_nutrition = Nutrition(
        product_id=nutrition.product_id,
        calories=nutrition.calories,
        sugar=nutrition.sugar,
        total_fat=nutrition.total_fat,
        saturated_fat=nutrition.saturated_fat,
        protein=nutrition.protein,
        carbohydrates=nutrition.carbohydrates,
        sodium=nutrition.sodium,
        fiber=nutrition.fiber
    )

    db.add(new_nutrition)
    db.commit()
    db.refresh(new_nutrition)

    return new_nutrition


@router.get("/{product_id}", response_model=NutritionResponse)
def get_nutrition(
    product_id: int,
    db: Session = Depends(get_db)
):

    nutrition = db.query(Nutrition).filter(
        Nutrition.product_id == product_id
    ).first()

    if nutrition is None:
        raise HTTPException(
            status_code=404,
            detail="Nutrition data not found"
        )

    return nutrition
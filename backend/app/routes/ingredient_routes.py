from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.schemas.ingredient_schema import (
    IngredientCreate,
    IngredientResponse
)


router = APIRouter(
    prefix="/ingredients",
    tags=["Ingredients"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=IngredientResponse)
def create_ingredient(
    ingredient: IngredientCreate,
    db: Session = Depends(get_db)
):

    # Check whether product exists
    product = db.query(Product).filter(
        Product.id == ingredient.product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    new_ingredient = Ingredient(
        product_id=ingredient.product_id,
        name=ingredient.name,
        category=ingredient.category,
        explanation=ingredient.explanation
    )

    db.add(new_ingredient)
    db.commit()
    db.refresh(new_ingredient)

    return new_ingredient


@router.get("/product/{product_id}", response_model=list[IngredientResponse])
def get_product_ingredients(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return db.query(Ingredient).filter(
        Ingredient.product_id == product_id
    ).all()
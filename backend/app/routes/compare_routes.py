from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analysis.health_scoring import to_per_100g
from app.analysis.ingredient_analyzer import analyze_ingredients
from app.database.connection import get_db
from app.models.product import Product
from app.schemas.product_schema import ProductResponse
from app.services.compare_service import compare_products
from app.services.health_score_service import compute_health

router = APIRouter(prefix="/compare", tags=["Compare"])

NUTRITION_FIELDS = [
    "calories", "carbohydrates", "protein", "total_fat", "saturated_fat",
    "trans_fat", "sugar", "sodium", "fiber", "cholesterol",
]


def _load(db, product_id):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found.")

    if product.nutrition is None:
        raise HTTPException(
            status_code=404,
            detail=f"'{product.product_name}' has no nutrition data to compare.")

    nutrition = {f: getattr(product.nutrition, f, None) for f in NUTRITION_FIELDS}
    data = ProductResponse.model_validate(product).model_dump()

    return {
        "id": product.id,
        "product_name": data.get("product_name"),
        "brand": data.get("brand"),
        "category": data.get("category"),
        "health": compute_health(data, nutrition),
        "per_100g": to_per_100g(nutrition, data.get("serving_size")),
        "ingredient_highlights": analyze_ingredients(data.get("ingredients"))["highlights"],
    }


@router.get("")
def compare(
    a: int = Query(..., description="Id of the first product"),
    b: int = Query(..., description="Id of the second product"),
    db: Session = Depends(get_db),
):
    if a == b:
        raise HTTPException(status_code=400, detail="Please choose two different products.")

    return compare_products(_load(db, a), _load(db, b))
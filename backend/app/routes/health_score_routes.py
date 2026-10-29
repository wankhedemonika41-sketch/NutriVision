import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.ingredient_analyzer import analyze_ingredients
from app.database.connection import get_db
from app.models.product import Product
from app.schemas.product_schema import ProductResponse
from app.services.barcode_service import fetch_off_product, map_off_product
from app.services.health_score_service import compute_health

router = APIRouter(prefix="/health-score", tags=["Health Score"])

NUTRITION_FIELDS = [
    "calories", "carbohydrates", "protein", "total_fat", "saturated_fat",
    "trans_fat", "sugar", "sodium", "fiber", "cholesterol",
]


def _nutrition_dict(product):
    if product.nutrition is None:
        return None
    return {f: getattr(product.nutrition, f, None) for f in NUTRITION_FIELDS}


@router.get("/product/{product_id}")
def product_health_score(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    nutrition = _nutrition_dict(product)
    if nutrition is None:
        raise HTTPException(status_code=404, detail="Nutrition data not available")

    product_data = ProductResponse.model_validate(product).model_dump()
    return compute_health(product_data, nutrition)


@router.get("/barcode/{barcode}")
def health_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """Barcode -> own database first, then Open Food Facts."""
    code = barcode.strip()

    if not code.isdigit() or not 6 <= len(code) <= 14:
        raise HTTPException(status_code=400, detail="A barcode contains 6 to 14 digits.")

    local = db.query(Product).filter(Product.barcode == code).first()

    if local is not None:
        source = "NutriVision database"
        product = ProductResponse.model_validate(local).model_dump()
        nutrition = _nutrition_dict(local)
        health = compute_health(product, nutrition)
    else:
        try:
            off = fetch_off_product(code)
        except requests.RequestException:
            raise HTTPException(
                status_code=502,
                detail="Could not reach Open Food Facts. Check your internet connection.",
            )

        if off is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found in the database or Open Food Facts.",
            )

        source = "Open Food Facts"
        product, nutrition = map_off_product(off)
        product["barcode"] = code
        health = compute_health(product, nutrition, already_per_100g=True)

    shown = (health or {}).get("per_100g") or nutrition

    return {
        "source": source,
        "product": product,
        "nutrition": shown,
        "ingredient_analysis": analyze_ingredients(product.get("ingredients")),
        "health": health,
    }
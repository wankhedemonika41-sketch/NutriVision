import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.product import Product
from app.schemas.product_schema import ProductResponse
from app.services.open_food_facts_service import (
    OpenFoodFactsError,
    get_product_from_open_food_facts,
    normalize_open_food_facts,
)
from app.services.report_service import build_report, nutrition_to_dict


router = APIRouter(
    prefix="/scan",
    tags=["Barcode Scan"]
)


@router.get("/{barcode}")
def scan_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    Find a product by barcode.
    1) NutriVision database  2) Open Food Facts (fallback)
    Returns the same shape as /products/details/{id}, plus "source".
    """

    barcode = barcode.strip()

    if not re.fullmatch(r"\d{6,14}", barcode):
        raise HTTPException(
            status_code=422,
            detail="A barcode contains 6 to 14 digits"
        )

    # ---- 1. local database ----------------------------------
    product = db.query(Product).filter(Product.barcode == barcode).first()

    if product is not None:
        product_data = ProductResponse.model_validate(product).model_dump()
        nutrition_data = nutrition_to_dict(product.nutrition)
        source = "NutriVision database"

    # ---- 2. Open Food Facts ---------------------------------
    else:
        try:
            raw = get_product_from_open_food_facts(barcode)
        except OpenFoodFactsError:
            raise HTTPException(
                status_code=502,
                detail="Open Food Facts is not reachable right now"
            )

        if raw is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found for this barcode"
            )

        normalized = normalize_open_food_facts(raw, barcode)
        product_data = normalized["product"]
        nutrition_data = normalized["nutrition"]
        source = "Open Food Facts"

    report = build_report(
    db, product_data, nutrition_data,
    already_per_100g=(source == "Open Food Facts"),
    )

    return {
        "source": source,
        "product": product_data,
        "nutrition": nutrition_data,
        "analysis": report["analysis"],
        "ingredient_analysis": report["ingredient_analysis"],
        "health": report["health"],
    }

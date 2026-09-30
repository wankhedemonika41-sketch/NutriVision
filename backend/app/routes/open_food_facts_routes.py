from fastapi import APIRouter, HTTPException

from app.services.open_food_facts_service import (
    get_product_from_open_food_facts
)


router = APIRouter(
    prefix="/external-products",
    tags=["Open Food Facts"]
)


@router.get("/{barcode}")
def get_external_product(barcode: str):
    product = get_product_from_open_food_facts(barcode)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found in Open Food Facts"
        )

    return product
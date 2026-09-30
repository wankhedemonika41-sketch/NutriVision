from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.product import Product
from app.models.nutrition import Nutrition
from app.models.reference_value import ReferenceValue

from app.analysis.nutrition_analyzer import analyze_nutrient


router = APIRouter(
    prefix="/analysis",
    tags=["Nutrition Analysis"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/nutrition/{product_id}")
def analyze_product_nutrition(
    product_id: int,
    db: Session = Depends(get_db)
):

    # ---------------------------------
    # 1. Find Product
    # ---------------------------------

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    # ---------------------------------
    # 2. Find Nutrition
    # ---------------------------------

    nutrition = db.query(Nutrition).filter(
        Nutrition.product_id == product_id
    ).first()

    if nutrition is None:
        raise HTTPException(
            status_code=404,
            detail="Nutrition data not found"
        )


    # ---------------------------------
    # 3. Get Reference Values
    # ---------------------------------

    references = db.query(ReferenceValue).all()

    if not references:
        raise HTTPException(
            status_code=404,
            detail="Reference values not found"
        )


    # ---------------------------------
    # 4. Create Reference Lookup
    # ---------------------------------

    reference_map = {
        ref.nutrient.lower(): {
            "value": ref.reference_value,
            "unit": ref.unit,
            "description": ref.description
        }
        for ref in references
    }


    # ---------------------------------
    # 5. Nutrient Mapping
    # ---------------------------------

    nutrient_mapping = {
        "sugar": nutrition.sugar,
        "sodium": nutrition.sodium,
        "total_fat": nutrition.total_fat,
        "saturated_fat": nutrition.saturated_fat,
        "protein": nutrition.protein,
        "fiber": nutrition.fiber,
        "calories": nutrition.calories
    }


    # ---------------------------------
    # 6. Analyze Each Nutrient
    # ---------------------------------

    results = {}

    for nutrient_name, value in nutrient_mapping.items():

        reference = reference_map.get(
            nutrient_name.lower()
        )

        if reference is None:

            results[nutrient_name] = {
                "value": value,
                "reference_value": None,
                "unit": None,
                "percentage": None,
                "level": "NO_REFERENCE",
                "description": None
            }

            continue


        analysis = analyze_nutrient(
            value=value,
            reference_value=reference["value"],
            unit=reference["unit"]
        )


        analysis["description"] = reference["description"]

        results[nutrient_name] = analysis


    # ---------------------------------
    # 7. Final Response
    # ---------------------------------

    return {
        "product_id": product.id,
        "product_name": product.product_name,
        "analysis": results
    }
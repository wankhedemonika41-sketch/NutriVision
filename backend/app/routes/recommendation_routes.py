from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.analysis.health_scoring import to_per_100g
from app.analysis.ingredient_analyzer import analyze_ingredients
from app.database.connection import get_db
from app.models.product import Product
from app.models.user import User
from app.routes.auth_routes import get_current_user
from app.routes.profile_routes import allergy_list
from app.schemas.product_schema import ProductResponse
from app.services.health_score_service import compute_health
from app.services.recommendation_service import recommend

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

MIN_SUBCATEGORY = 5     # fewer similar products than this -> use the whole category

NUTRITION_FIELDS = [
    "calories", "carbohydrates", "protein", "total_fat", "saturated_fat",
    "trans_fat", "sugar", "sodium", "fiber", "cholesterol",
]


def _prepare(product):
    """Product row -> plain dict used by the recommendation logic."""
    nutrition = {f: getattr(product.nutrition, f, None) for f in NUTRITION_FIELDS}
    data = ProductResponse.model_validate(product).model_dump()
    analysis = analyze_ingredients(data.get("ingredients"))

    return {
        "id": product.id,
        "product_name": data.get("product_name"),
        "brand": data.get("brand"),
        "category": data.get("category"),
        "price_inr": data.get("price_inr"),
        "ingredients": data.get("ingredients"),
        "health": compute_health(data, nutrition, explain=False),
        "per_100g": to_per_100g(nutrition, data.get("serving_size")),
        "allergens": analysis["allergens"],
        "highlights": analysis["highlights"],
    }


def _candidates(db, product):
    """Same sub-category when it is big enough, else the whole category."""
    query = (
        db.query(Product)
        .options(joinedload(Product.nutrition))
        .filter(Product.id != product.id)
    )

    if product.category and product.sub_category:
        rows = [
            row for row in query.filter(
                Product.category == product.category,
                Product.sub_category == product.sub_category).all()
            if row.nutrition is not None
        ]
        if len(rows) >= MIN_SUBCATEGORY:
            return rows, f"{len(rows)} similar products ({product.sub_category.title()})"

    if product.category:
        rows = [
            row for row in query.filter(Product.category == product.category).all()
            if row.nutrition is not None
        ]
        return rows, f"{len(rows)} products in {product.category.title()}"

    return [], None


@router.get("/{product_id}")
def recommendations(
    product_id: int,
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .options(joinedload(Product.nutrition))
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")

    if product.nutrition is None:
        raise HTTPException(
            status_code=404,
            detail="This product has no nutrition data, so it cannot be scored.")

    profile = {
        "diet": user.diet_preference,
        "allergies": allergy_list(user),
        "goal": user.health_goal,
    }

    target = _prepare(product)

    rows, compared_with = _candidates(db, product)
    candidates = [_prepare(row) for row in rows]

    result = recommend(target, candidates, profile, limit)

    if not product.category:
        result["message"] = "This product has no category, so alternatives cannot be suggested."

    result["compared_with"] = compared_with

    result["profile_used"] = {
        **profile,
        "personalised": bool(
            profile["allergies"]
            or profile["diet"] not in (None, "no_preference")
            or profile["goal"] not in (None, "general")
        ),
    }

    return result
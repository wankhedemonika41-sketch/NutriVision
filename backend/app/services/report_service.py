from sqlalchemy.orm import Session

from app.analysis.ingredient_analyzer import analyze_ingredients
from app.analysis.nutrition_analyzer import NUTRIENTS, analyze_nutrition
from app.models.reference_value import ReferenceValue
from app.services.health_score_service import compute_health

def load_references(db: Session) -> dict:
    """nutrient name -> daily reference value, from the database."""

    return {
        row.nutrient.lower(): row.reference_value
        for row in db.query(ReferenceValue).all()
    }


def nutrition_to_dict(nutrition) -> dict | None:
    """Turn a Nutrition ORM row into a plain dict (or None)."""

    if nutrition is None:
        return None

    data = {key: getattr(nutrition, key, None) for key in NUTRIENTS}
    data["vitamin"] = getattr(nutrition, "vitamin", None)

    return data


def build_report(db: Session, product: dict, nutrition: dict | None,
                 already_per_100g: bool = False) -> dict:
    analysis = None

    if nutrition:
        analysis = analyze_nutrition(
            nutrition=nutrition,
            category=product.get("category"),
            serving_size=product.get("serving_size"),
            references=load_references(db),
        )

    return {
        "analysis": analysis,
        "ingredient_analysis": analyze_ingredients(product.get("ingredients")),
        "health": compute_health(product, nutrition, already_per_100g),
    }
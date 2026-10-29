"""
Turns (per-100g nutrition + ingredient text + category) into the numeric
feature dict used by the Health Score model.
Same code is used for training and for live prediction.
"""

from app.analysis.ingredient_analyzer import analyze_ingredients

NUTRIENT_COLUMNS = [
    "calories", "carbohydrates", "protein", "total_fat", "saturated_fat",
    "trans_fat", "sugar", "sodium", "fiber", "cholesterol",
]

FLAG_TYPES = [
    "palm_oil", "added_sugar", "hydrogenated", "synthetic_colour",
    "artificial_flavour", "preservative", "whole_grain",
]

DRINK_CATEGORIES = {"JUICE", "BEVERAGE", "BEVERAGES", "DRINK", "DRINKS"}

FEATURE_COLUMNS = (
    NUTRIENT_COLUMNS
    + ["ingredient_count", "n_caution_flags", "n_info_flags", "n_positive_flags"]
    + ["has_" + t for t in FLAG_TYPES]
    + ["is_drink"]
)

FEATURE_LABELS = {
    "calories": "Calories", "carbohydrates": "Carbohydrates",
    "protein": "Protein", "total_fat": "Total fat",
    "saturated_fat": "Saturated fat", "trans_fat": "Trans fat",
    "sugar": "Sugar", "sodium": "Sodium", "fiber": "Fibre",
    "cholesterol": "Cholesterol",
    "ingredient_count": "Number of ingredients",
    "n_caution_flags": "Cautionary ingredients",
    "n_info_flags": "Additives / processing markers",
    "n_positive_flags": "Wholesome ingredients",
    "has_palm_oil": "Palm oil", "has_added_sugar": "Added sugar",
    "has_hydrogenated": "Hydrogenated fat",
    "has_synthetic_colour": "Synthetic colour",
    "has_artificial_flavour": "Artificial flavour",
    "has_preservative": "Preservative", "has_whole_grain": "Whole grain",
    "is_drink": "Drink category",
}


def build_features(per100, ingredients_text, category):
    ing = analyze_ingredients(ingredients_text)
    highlights = ing["highlights"]
    found = {h["type"] for h in highlights}

    features = {c: float(per100.get(c) or 0.0) for c in NUTRIENT_COLUMNS}

    features["ingredient_count"] = ing["count"]
    features["n_caution_flags"] = sum(1 for h in highlights if h["severity"] == "caution")
    features["n_info_flags"] = sum(1 for h in highlights if h["severity"] == "info")
    features["n_positive_flags"] = sum(1 for h in highlights if h["severity"] == "positive")

    for flag in FLAG_TYPES:
        features["has_" + flag] = int(flag in found)

    features["is_drink"] = int(str(category or "").strip().upper() in DRINK_CATEGORIES)

    return features
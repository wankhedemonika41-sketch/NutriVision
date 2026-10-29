"""
Health Score (0-100), grade and indicative risk flags.

Per-100g based, loosely inspired by Nutri-Score (energy, sugar, saturated
fat, sodium, fibre, protein) plus an ingredient adjustment.
These are educational indicators, NOT medical advice.
"""

import re

PER100_KEYS = [
    "calories", "carbohydrates", "protein", "total_fat", "saturated_fat",
    "trans_fat", "sugar", "sodium", "fiber", "cholesterol",
]

# (minimum score, grade, label)
GRADES = [
    (75, "A", "Healthy choice"),
    (55, "B", "Okay in moderation"),
    (35, "C", "Limit this food"),
    (0,  "D", "Occasional treat only"),
]


def parse_serving(value):
    """100, 100.0, '100 g', '30g' -> float. Anything else -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    match = re.search(r"\d+(?:[.,]\d+)?", str(value))
    if not match:
        return None
    number = float(match.group().replace(",", "."))
    return number if number > 0 else None


def to_per_100g(nutrition, serving_size, already_per_100g=False):
    """
    The dataset mixes per-100g rows and per-serving rows.
    Rule: if serving != 100 g, scale to 100 g, unless that gives an
    impossible energy value (> 900 kcal/100 g) - then it was already per 100 g.
    """
    data = {key: nutrition.get(key) for key in PER100_KEYS}

    if already_per_100g:
        return data

    serving = parse_serving(serving_size)
    if serving is None or abs(serving - 100) < 1e-9:
        return data

    factor = 100.0 / serving
    calories = data.get("calories")
    if calories is None or calories * factor > 900:
        return data

    return {
        key: (None if value is None else round(value * factor, 2))
        for key, value in data.items()
    }


def grade_for(score):
    for minimum, grade, label in GRADES:
        if score >= minimum:
            return grade, label
    return "D", GRADES[-1][2]


def compute_health_score(f):
    """
    f = feature dict (see health_features.build_features).
    Returns score 0-100 (higher = healthier) with a breakdown.
    """
    drink = bool(f.get("is_drink"))

    kj = f.get("calories", 0) * 4.184
    energy_pts = min(10, int(kj / (60 if drink else 335)))
    sugar_pts = min(10, int(f.get("sugar", 0) / (1.5 if drink else 4.5)))
    satfat_pts = min(10, int(f.get("saturated_fat", 0) / 1.0))
    sodium_pts = min(10, int(f.get("sodium", 0) / 90))
    trans_pts = min(5, int(f.get("trans_fat", 0) / 0.2))
    negative = energy_pts + sugar_pts + satfat_pts + sodium_pts + trans_pts

    fibre_pts = min(5, int(f.get("fiber", 0) / 0.9))
    protein_pts = min(5, int(f.get("protein", 0) / 1.6))
    positive = fibre_pts + protein_pts

    raw = negative - positive                      # -10 ... +45
    nutrient_score = 100.0 * (45 - raw) / 55.0

    ingredient_penalty = min(
        20.0,
        4.0 * f.get("n_caution_flags", 0) + 1.5 * f.get("n_info_flags", 0),
    )
    ingredient_bonus = min(5.0, 3.0 * f.get("n_positive_flags", 0))

    score = nutrient_score - ingredient_penalty + ingredient_bonus
    score = max(0.0, min(100.0, score))
    grade, label = grade_for(score)

    return {
        "score": round(score, 1),
        "grade": grade,
        "label": label,
        "parts": {
            "negative_points": negative,
            "positive_points": positive,
            "ingredient_penalty": round(ingredient_penalty, 1),
            "ingredient_bonus": round(ingredient_bonus, 1),
        },
    }


def _level(value, medium, high):
    if value >= high:
        return "HIGH"
    if value >= medium:
        return "MEDIUM"
    return "LOW"


_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def _worst(*levels):
    return max(levels, key=lambda lv: _ORDER[lv])


def risk_flags(f):
    """
    Indicative risk levels from nutrient content per 100 g
    (UK/FSSAI-style traffic-light thresholds). NOT a diagnosis.
    """
    drink = bool(f.get("is_drink"))

    sugar = f.get("sugar", 0)
    diabetes = _level(sugar, 2.5 if drink else 5, 11.25 if drink else 22.5)

    sat = f.get("saturated_fat", 0)
    trans = f.get("trans_fat", 0)
    heart = _worst(_level(sat, 1.5, 5), _level(trans, 0.2, 0.5))

    sodium = f.get("sodium", 0)
    bp = _level(sodium, 120, 600)

    cal = f.get("calories", 0)
    fat = f.get("total_fat", 0)
    obesity = _worst(_level(cal, 250, 400), _level(fat, 3, 17.5))

    return {
        "diabetes_risk": {
            "level": diabetes,
            "reason": f"Sugar is {sugar:g} g per 100 g.",
        },
        "heart_risk": {
            "level": heart,
            "reason": f"Saturated fat {sat:g} g and trans fat {trans:g} g per 100 g.",
        },
        "blood_pressure_risk": {
            "level": bp,
            "reason": f"Sodium is {sodium:g} mg per 100 g.",
        },
        "obesity_risk": {
            "level": obesity,
            "reason": f"Energy {cal:g} kcal and fat {fat:g} g per 100 g.",
        },
    }
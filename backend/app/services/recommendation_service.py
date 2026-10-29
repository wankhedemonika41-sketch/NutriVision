"""
Healthier alternatives for a product.

Pure logic (no database): the route prepares plain dicts, this module decides
which products are better, safe for the user, and why.

Diet filtering is ESTIMATED from the ingredient text because the dataset has
no veg / non-veg marker. Allergen filtering is keyword based. The app always
tells the user to check the pack.
"""

import re

from app.services.compare_service import (
    NUTRIENT_ROWS, change_size, describe_change, is_meaningful,
)

MIN_GAIN = 8.0            # an alternative must score at least this much higher
MAX_GOAL_BONUS = 15.0     # the goal can move a product up the list, but only a bit
SWEETENER_PENALTY = 5.0   # artificial sweeteners rank a little lower (not for a sugar goal)
HEALTHY_SCORE = 75        # grade A: no alternatives needed

GOAL_KEYS = {
    "lose_weight":  ["calories", "total_fat"],
    "manage_sugar": ["sugar"],
    "heart_health": ["saturated_fat", "sodium", "trans_fat"],
    "build_muscle": ["protein", "fiber"],
}

_MEAT = re.compile(
    r"chicken|mutton|\bbeef\b|\bpork\b|\blamb\b|\bmeat\b|bacon|\bham\b|"
    r"sausage|salami|pepperoni|\blard\b|tallow|suet|keema", re.I)
_FISH = re.compile(
    r"\bfish\b|prawn|shrimp|\btuna\b|anchov|\bcrab\b|squid|shellfish|surimi", re.I)
_ANIMAL_OTHER = re.compile(
    r"gelatin|carmine|cochineal|\b(?:INS|E)[\s-]?120\b|rennet|isinglass", re.I)
_EGG_EXTRA = re.compile(r"albumen|mayonnaise", re.I)
_HONEY = re.compile(r"\bhoney\b", re.I)


def has_ingredients(text):
    return bool(text and len(text.strip()) >= 3)


def diet_problem(diet, ingredients, allergens):
    """None if the product fits the diet, else 'unknown' or a short reason."""
    if diet in (None, "no_preference", "non_vegetarian"):
        return None

    if not has_ingredients(ingredients):
        return "unknown"

    if _MEAT.search(ingredients) or _FISH.search(ingredients) \
            or _ANIMAL_OTHER.search(ingredients):
        return "contains meat, fish or gelatin"

    has_egg = "Egg" in allergens or bool(_EGG_EXTRA.search(ingredients))

    if diet == "vegetarian" and has_egg:
        return "contains egg"

    if diet == "vegan":
        if has_egg:
            return "contains egg"
        if "Milk" in allergens:
            return "contains milk"
        if _HONEY.search(ingredients):
            return "contains honey"

    return None


def _improvements(target, candidate):
    """Nutrients where the candidate is clearly better, most important first."""
    found = []
    for key, label, unit, direction in NUTRIENT_ROWS:
        if direction is None:
            continue
        t, c = target.get(key), candidate.get(key)
        if t is None or c is None:
            continue
        better = c < t if direction == "lower" else c > t
        if not better or not is_meaningful(key, direction, c, t):
            continue
        found.append({
            "key": key,
            "size": change_size(direction, c, t),
            "text": describe_change(label, unit, direction, c, t),
        })
    return sorted(found, key=lambda item: item["size"], reverse=True)


def _summary(product):
    health = product.get("health") or {}
    return {
        "id": product.get("id"),
        "product_name": product.get("product_name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "score": health.get("score"),
        "grade": health.get("grade"),
    }


def _has_sweetener(candidate):
    return any(h.get("type") == "sweetener" for h in candidate.get("highlights", []))


def recommend(target, candidates, profile, limit=5):
    """
    target / candidates: dicts with id, product_name, brand, category,
        price_inr, health (compute_health result), per_100g, ingredients,
        allergens (list), highlights (list of {type, label, severity}).
    profile: {"diet": str | None, "allergies": [names], "goal": str | None}
    """
    health = target.get("health") or {}
    target_score = health.get("score") if health.get("available") else None

    base = {
        "product": _summary(target),
        "recommendations": [],
        "excluded": {"allergen": 0, "diet": 0, "unknown_ingredients": 0},
        "checked": 0,
        "notes": [],
        "message": None,
    }

    if target_score is None:
        base["message"] = ("A health score could not be calculated for this "
                           "product, so alternatives cannot be suggested.")
        return base

    if target_score >= HEALTHY_SCORE:
        base["message"] = ("This is already a healthy choice (grade A), so "
                           "no alternatives are needed.")
        return base

    allergies = set(profile.get("allergies") or [])
    diet = profile.get("diet")
    goal = profile.get("goal")
    goal_keys = GOAL_KEYS.get(goal, [])
    target_name = (target.get("product_name") or "").strip().lower()
    needs_text = bool(allergies) or diet not in (None, "no_preference", "non_vegetarian")

    excluded = base["excluded"]
    kept = []

    for cand in candidates:
        if cand.get("id") == target.get("id"):
            continue
        if (cand.get("product_name") or "").strip().lower() == target_name:
            continue                         # same product, another pack size

        cand_health = cand.get("health") or {}
        if not cand_health.get("available"):
            continue

        base["checked"] += 1

        gain = cand_health["score"] - target_score
        if gain < MIN_GAIN:
            continue

        # ---- safety filters (only for products that would be suggested) ----
        if needs_text and not has_ingredients(cand.get("ingredients")):
            excluded["unknown_ingredients"] += 1
            continue

        if allergies & set(cand.get("allergens") or []):
            excluded["allergen"] += 1
            continue

        if diet_problem(diet, cand.get("ingredients"), cand.get("allergens") or []):
            excluded["diet"] += 1
            continue

        improvements = _improvements(target.get("per_100g") or {}, cand.get("per_100g") or {})
        goal_hits = [i for i in improvements if i["key"] in goal_keys]
        others = [i for i in improvements if i["key"] not in goal_keys]

        bonus = min(MAX_GOAL_BONUS, 0.15 * goal_hits[0]["size"]) if goal_hits else 0.0

        sweetener = _has_sweetener(cand)
        penalty = SWEETENER_PENALTY if sweetener and goal != "manage_sugar" else 0.0

        kept.append({
            "rank": gain + bonus - penalty,
            "item": {
                "id": cand["id"],
                "product_name": cand.get("product_name"),
                "brand": cand.get("brand"),
                "category": cand.get("category"),
                "price_inr": cand.get("price_inr"),
                "score": cand_health["score"],
                "grade": cand_health["grade"],
                "score_gain": round(gain, 1),
                "reasons": [i["text"] for i in (goal_hits + others)[:3]],
                "goal_match": ("Fits your goal: " + goal_hits[0]["text"]) if goal_hits else None,
                "contains_sweetener": sweetener,
                "cautions": [h["label"] for h in cand.get("highlights", [])
                             if h.get("severity") == "caution"][:3],
            },
        })

    kept.sort(key=lambda row: row["rank"], reverse=True)

    seen, results = set(), []
    for row in kept:                          # one entry per product name
        name = (row["item"]["product_name"] or "").strip().lower()
        if name in seen:
            continue
        seen.add(name)
        results.append(row["item"])
        if len(results) == limit:
            break

    base["recommendations"] = results

    # ---- explain what was left out ----
    if excluded["allergen"]:
        base["notes"].append(
            f"{excluded['allergen']} healthier product(s) were left out because "
            f"they may contain your allergens ({', '.join(sorted(allergies))}).")
    if excluded["diet"]:
        base["notes"].append(
            f"{excluded['diet']} healthier product(s) were left out because they "
            "do not seem to fit your diet (estimated from the ingredients).")
    if excluded["unknown_ingredients"]:
        base["notes"].append(
            f"{excluded['unknown_ingredients']} healthier product(s) were left out "
            "because their ingredients are unknown, so they cannot be checked.")

    if not results:
        if sum(excluded.values()):
            base["message"] = ("No suitable alternatives were found. Healthier "
                               "products exist but do not match your allergies "
                               "or diet.")
        elif base["checked"] < 3:
            base["message"] = ("There are very few similar products in our "
                               "database, so no alternatives were found.")
        else:
            base["message"] = ("No clearly healthier alternatives were found "
                               "among similar products.")

    return base
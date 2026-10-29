"""
Side-by-side comparison of two products (all values per 100 g).
Pure logic, no database, so it is easy to test.
"""

# key, label, unit, which direction is healthier (None = no judgement)
NUTRIENT_ROWS = [
    ("calories",      "Calories",      "kcal", "lower"),
    ("sugar",         "Sugar",         "g",    "lower"),
    ("sodium",        "Sodium",        "mg",   "lower"),
    ("saturated_fat", "Saturated fat", "g",    "lower"),
    ("trans_fat",     "Trans fat",     "g",    "lower"),
    ("total_fat",     "Total fat",     "g",    "lower"),
    ("carbohydrates", "Carbohydrates", "g",    None),
    ("protein",       "Protein",       "g",    "higher"),
    ("fiber",         "Fibre",         "g",    "higher"),
    ("cholesterol",   "Cholesterol",   "mg",   "lower"),
]

RISK_ROWS = [
    ("diabetes_risk",       "Diabetes (sugar)"),
    ("heart_risk",          "Heart (fat)"),
    ("blood_pressure_risk", "Blood pressure (sodium)"),
    ("obesity_risk",        "Obesity (energy)"),
]

_LEVEL = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

CLOSE_SCORE_POINTS = 3     # scores closer than this = "too close to call"
MIN_REASON_PERCENT = 15    # only mention differences of at least this size

# A difference smaller than this (in the nutrient's own unit) is not worth
# mentioning, even if it looks big in percent (e.g. trans fat 0.1 g vs 0 g).
MIN_ABSOLUTE_CHANGE = {
    "calories": 20, "sugar": 1, "sodium": 20, "saturated_fat": 0.5,
    "trans_fat": 0.2, "total_fat": 1, "protein": 1, "fiber": 1,
    "cholesterol": 5,
}


def change_percent(direction, better, worse):
    """
    How much better `better` is than `worse`, as a percent of the baseline
    (`worse`). None when the baseline is 0 (an increase from nothing).
    """
    if worse <= 0:
        return None
    if direction == "lower":
        return (worse - better) / worse * 100
    return (better - worse) / worse * 100


def is_meaningful(key, direction, better, worse):
    """Big enough, in absolute terms and in percent, to be worth saying."""
    if abs(better - worse) < MIN_ABSOLUTE_CHANGE.get(key, 0):
        return False
    percent = change_percent(direction, better, worse)
    return percent is None or percent >= MIN_REASON_PERCENT


def change_size(direction, better, worse):
    """0-100 number used only to sort differences by importance."""
    percent = change_percent(direction, better, worse)
    if percent is None:              # from "none" to something: real, but not the headline
        return 60.0
    return min(percent, 100.0)


def describe_change(label, unit, direction, better, worse):
    """One honest sentence about a nutrient difference."""
    verb = "are" if label.lower() == "calories" else "is"
    where = f"{better:g} vs {worse:g} {unit} per 100 g"

    if direction == "lower":
        if better == 0:
            return f"{label} {verb} zero ({where})"
        return f"{label} {verb} {change_percent(direction, better, worse):.0f}% lower ({where})"

    if worse == 0:
        return f"{label} {verb} {better:g} {unit} per 100 g (vs none)"

    ratio = better / worse
    if ratio >= 2:
        times = ("%.1f" % ratio).rstrip("0").rstrip(".")
        return f"{label} {verb} {times}x higher ({where})"
    return f"{label} {verb} {change_percent(direction, better, worse):.0f}% higher ({where})"


def _pick(a, b, direction):
    """Which side is healthier for one nutrient: 'a', 'b', 'tie' or None."""
    if a is None or b is None or direction is None:
        return None

    diff = abs(a - b)
    if diff < 0.05 or diff < 0.05 * max(a, b):
        return "tie"

    if direction == "lower":
        return "a" if a < b else "b"
    return "a" if a > b else "b"


def _side(product):
    health = product.get("health") or {}
    available = bool(health.get("available"))
    return {
        "id": product.get("id"),
        "product_name": product.get("product_name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "available": available,
        "score": health.get("score") if available else None,
        "grade": health.get("grade") if available else None,
        "label": health.get("label") if available else None,
        "unavailable_reason": None if available else health.get("reason"),
        "flags": [
            {"label": h["label"], "severity": h["severity"]}
            for h in product.get("ingredient_highlights", [])
        ],
    }


def compare_products(a, b):
    per_a = a.get("per_100g") or {}
    per_b = b.get("per_100g") or {}

    rows = []
    for key, label, unit, direction in NUTRIENT_ROWS:
        va, vb = per_a.get(key), per_b.get(key)
        rows.append({
            "key": key, "label": label, "unit": unit,
            "a": va, "b": vb,
            "better": _pick(va, vb, direction),
            "direction": direction,
        })

    risks = []
    ha = (a.get("health") or {}).get("risks") or {}
    hb = (b.get("health") or {}).get("risks") or {}
    for key, label in RISK_ROWS:
        la = ha.get(key, {}).get("level")
        lb = hb.get(key, {}).get("level")
        if la is None or lb is None:
            better = None
        elif _LEVEL[la] == _LEVEL[lb]:
            better = "tie"
        else:
            better = "a" if _LEVEL[la] < _LEVEL[lb] else "b"
        risks.append({"key": key, "label": label, "a": la, "b": lb, "better": better})

    side_a, side_b = _side(a), _side(b)
    sa, sb = side_a["score"], side_b["score"]

    if sa is None or sb is None:
        winner, difference = "unknown", None
        summary = ("A health score could not be calculated for one of the "
                   "products, so they cannot be ranked.")
    else:
        difference = round(abs(sa - sb), 1)
        if difference < CLOSE_SCORE_POINTS:
            winner = "tie"
            summary = (f"Both products are very close ({sa:g} vs {sb:g}). "
                       "Neither is clearly healthier.")
        else:
            winner = "a" if sa > sb else "b"
            best = side_a if winner == "a" else side_b
            other = side_b if winner == "a" else side_a
            summary = (f"{best['product_name']} is the healthier choice "
                       f"(score {best['score']:g} vs {other['score']:g}).")

    reasons = []
    if winner in ("a", "b"):
        loser = "b" if winner == "a" else "a"
        candidates = []
        for row in rows:
            if row["better"] != winner or row["direction"] is None:
                continue
            better, worse = row[winner], row[loser]
            if not is_meaningful(row["key"], row["direction"], better, worse):
                continue
            candidates.append((
                change_size(row["direction"], better, worse),
                describe_change(row["label"], row["unit"], row["direction"], better, worse),
            ))
        candidates.sort(key=lambda item: item[0], reverse=True)
        reasons = [text for _, text in candidates[:3]]

    return {
        "a": side_a,
        "b": side_b,
        "winner": winner,
        "score_difference": difference,
        "summary": summary,
        "reasons": reasons,
        "nutrition": rows,
        "risks": risks,
        "disclaimer": (
            "Comparison of nutrient and ingredient content per 100 g. "
            "It is general information, not medical advice."),
    }
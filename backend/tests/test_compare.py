from app.services.compare_service import compare_products


def _product(pid, name, score, per100, risks=None, flags=None, available=True):
    health = {"available": available}
    if available:
        health.update({
            "score": score,
            "grade": "A" if score >= 75 else "C",
            "label": "x",
            "risks": risks or {},
        })
    else:
        health["reason"] = "Calories, sugar and sodium are needed."
    return {
        "id": pid, "product_name": name, "brand": None, "category": "SNACKS",
        "health": health, "per_100g": per100,
        "ingredient_highlights": flags or [],
    }


SWEET = {"calories": 480, "sugar": 30, "sodium": 300, "saturated_fat": 9,
         "protein": 6, "fiber": 1}
LIGHT = {"calories": 430, "sugar": 12, "sodium": 150, "saturated_fat": 2,
         "protein": 9, "fiber": 7}


def test_higher_score_wins():
    r = compare_products(_product(1, "Sweet", 36, SWEET), _product(2, "Light", 81, LIGHT))
    assert r["winner"] == "b"
    assert r["score_difference"] == 45
    assert "Light" in r["summary"]


def test_close_scores_are_a_tie():
    r = compare_products(_product(1, "A", 60, SWEET), _product(2, "B", 62, LIGHT))
    assert r["winner"] == "tie"


def test_lower_sugar_and_higher_fibre_are_marked_better():
    r = compare_products(_product(1, "Sweet", 36, SWEET), _product(2, "Light", 81, LIGHT))
    rows = {row["key"]: row for row in r["nutrition"]}
    assert rows["sugar"]["better"] == "b"
    assert rows["fiber"]["better"] == "b"
    assert rows["protein"]["better"] == "b"


def test_tiny_difference_is_a_tie():
    a = dict(SWEET, sodium=300)
    b = dict(SWEET, sodium=305)
    r = compare_products(_product(1, "A", 50, a), _product(2, "B", 80, b))
    assert {row["key"]: row for row in r["nutrition"]}["sodium"]["better"] == "tie"


def test_reasons_describe_the_winner_in_numbers():
    r = compare_products(_product(1, "Sweet", 36, SWEET), _product(2, "Light", 81, LIGHT))
    assert 1 <= len(r["reasons"]) <= 3
    assert any("Sugar is 60% lower" in text for text in r["reasons"])


def test_carbohydrates_are_not_judged():
    r = compare_products(
        _product(1, "A", 40, dict(SWEET, carbohydrates=70)),
        _product(2, "B", 80, dict(LIGHT, carbohydrates=40)))
    rows = {row["key"]: row for row in r["nutrition"]}
    assert rows["carbohydrates"]["better"] is None


def test_missing_value_gives_no_winner_for_that_row():
    r = compare_products(
        _product(1, "A", 40, {"sugar": 5}), _product(2, "B", 80, {"sugar": None}))
    assert {row["key"]: row for row in r["nutrition"]}["sugar"]["better"] is None


def test_unavailable_score_means_unknown_winner():
    r = compare_products(
        _product(1, "A", 0, SWEET, available=False), _product(2, "B", 80, LIGHT))
    assert r["winner"] == "unknown"
    assert r["a"]["score"] is None
    assert r["a"]["unavailable_reason"]


def test_risk_levels_are_compared():
    low = {"diabetes_risk": {"level": "LOW"}}
    high = {"diabetes_risk": {"level": "HIGH"}}
    r = compare_products(
        _product(1, "A", 40, SWEET, risks=high), _product(2, "B", 80, LIGHT, risks=low))
    diabetes = [x for x in r["risks"] if x["key"] == "diabetes_risk"][0]
    assert diabetes["better"] == "b"
    
    


# ---------------- wording (added after a real-data review) ----------------

from app.services.compare_service import (
    change_percent, describe_change, is_meaningful,
)


def test_higher_is_measured_against_the_lower_baseline():
    # 7 g fibre vs 1 g is 7 times as much, not "86 % higher"
    assert describe_change("Fibre", "g", "higher", 7, 1) == "Fibre is 7x higher (7 vs 1 g per 100 g)"
    assert describe_change("Protein", "g", "higher", 9, 6) == "Protein is 50% higher (9 vs 6 g per 100 g)"
    assert change_percent("higher", 9, 6) == 50


def test_lower_is_measured_against_the_original():
    assert describe_change("Sugar", "g", "lower", 12, 30) == "Sugar is 60% lower (12 vs 30 g per 100 g)"


def test_zero_values_get_plain_wording():
    assert describe_change("Sugar", "g", "lower", 0, 55.5) == "Sugar is zero (0 vs 55.5 g per 100 g)"
    assert describe_change("Fibre", "g", "higher", 8, 0) == "Fibre is 8 g per 100 g (vs none)"
    assert describe_change("Calories", "kcal", "lower", 31, 62.9).startswith("Calories are 51% lower")


def test_tiny_absolute_differences_are_not_worth_mentioning():
    assert not is_meaningful("trans_fat", "lower", 0, 0.1)      # 100 % but only 0.1 g
    assert not is_meaningful("sugar", "lower", 10.5, 11)        # under 1 g
    assert is_meaningful("sugar", "lower", 5, 30)
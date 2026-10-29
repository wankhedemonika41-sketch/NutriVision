from app.analysis.health_features import build_features
from app.analysis.health_scoring import compute_health_score, risk_flags, to_per_100g


def _score(nutrition, ingredients, category="SNACKS"):
    return compute_health_score(build_features(nutrition, ingredients, category))["score"]


OATS = dict(calories=380, carbohydrates=66, protein=13, total_fat=7, saturated_fat=1.2,
            trans_fat=0, sugar=1, sodium=5, fiber=10, cholesterol=0)
CHOCOLATE = dict(calories=550, carbohydrates=58, protein=6, total_fat=32, saturated_fat=18,
                 trans_fat=0.1, sugar=50, sodium=50, fiber=1, cholesterol=10)


def test_score_range():
    for n, ing in [(OATS, "Rolled oats"), (CHOCOLATE, "Sugar, palm oil, cocoa butter")]:
        assert 0 <= _score(n, ing) <= 100


def test_oats_much_healthier_than_chocolate():
    oats = _score(OATS, "Rolled oats")
    choc = _score(CHOCOLATE, "Sugar, palm oil, cocoa butter, emulsifier (lecithin)")
    assert oats > choc + 30


def test_per_serving_row_is_scaled_to_100g():
    out = to_per_100g({"calories": 105, "sugar": 6.8}, 20)
    assert out["calories"] == 525.0
    assert out["sugar"] == 34.0


def test_per_100g_row_unchanged():
    assert to_per_100g({"calories": 479}, 100)["calories"] == 479


def test_impossible_scaling_keeps_original():
    # 479 kcal with a 30 g serving would become 1596 kcal/100 g -> keep as is
    assert to_per_100g({"calories": 479}, 30)["calories"] == 479


def test_high_sodium_flags_bp_risk():
    f = build_features(dict(OATS, sodium=800), "Rolled oats", "SNACKS")
    assert risk_flags(f)["blood_pressure_risk"]["level"] == "HIGH"


def test_drink_is_judged_more_strictly():
    juice = dict(calories=45, carbohydrates=11, protein=0, total_fat=0, saturated_fat=0,
                 trans_fat=0, sugar=10, sodium=5, fiber=0, cholesterol=0)
    as_drink = _score(juice, "Water, sugar", "JUICE")
    as_snack = _score(juice, "Water, sugar", "SNACKS")
    assert as_drink < as_snack
from app.analysis.ingredient_analyzer import (
    analyze_ingredients, flatten_ingredients, split_ingredients
)
from app.analysis.nutrition_analyzer import analyze_nutrition, parse_serving
from app.services.data_cleaning import clean_name, parse_number


# ---------------- number cleaning ----------------

def test_parse_number_variants():
    assert parse_number(12.5) == (12.5, None)
    assert parse_number("7,65") == (7.65, None)
    assert parse_number("<1") == (0.5, "trace")
    assert parse_number("5.928.8") == (None, "invalid")
    assert parse_number("") == (None, None)
    assert parse_number(None) == (None, None)


def test_clean_name():
    assert clean_name("HIDE & SEEK\u00ae\u00a0 ") == "HIDE & SEEK"


# ---------------- nutrition analysis ----------------

def test_parse_serving():
    assert parse_serving("30 g") == (30.0, "g")
    assert parse_serving("250 ml") == (250.0, "ml")
    assert parse_serving("1 pack") == (None, "g")   # no weight -> unknown
    assert parse_serving("100") == (100.0, "g")
    assert parse_serving("100g (1 pack)") == (100.0, "g")
    assert parse_serving("pack") == (None, "g")
    assert parse_serving(None) == (None, "g")


def test_per_serving_values_are_normalised_to_100g():
    # 20 g serving with 6.8 g sugar -> 34 g per 100 g -> HIGH
    result = analyze_nutrition(
        {"sugar": 6.8, "calories": 105},
        category="BISCUIT",
        serving_size="20 g",
    )
    sugar = result["nutrients"]["sugar"]
    assert sugar["per_100"] == 34.0
    assert sugar["level"] == "HIGH"
    assert sugar["rating"] == "limit"


def test_high_fibre_is_good_and_low_sugar_is_good():
    result = analyze_nutrition(
        {"fiber": 8, "sugar": 2, "calories": 300},
        category="SNACKS",
        serving_size="100 g",
        references={"fiber": 28},
    )
    assert result["nutrients"]["fiber"]["rating"] == "good"
    assert result["nutrients"]["sugar"]["rating"] == "good"
    assert result["nutrients"]["fiber"]["percent_daily_value"] == 28.6


def test_drinks_use_stricter_limits():
    food = analyze_nutrition({"sugar": 8}, category="SNACKS", serving_size="100 g")
    drink = analyze_nutrition({"sugar": 8}, category="JUICE", serving_size="100 ml")
    assert food["nutrients"]["sugar"]["level"] == "MEDIUM"
    assert drink["nutrients"]["sugar"]["level"] == "MEDIUM"
    drink_high = analyze_nutrition({"sugar": 12}, category="JUICE", serving_size="100 ml")
    assert drink_high["nutrients"]["sugar"]["level"] == "HIGH"
    assert drink["basis"] == "per 100 ml"


def test_missing_values_are_unknown():
    result = analyze_nutrition({"sugar": None}, serving_size="100 g")
    assert result["nutrients"]["sugar"]["level"] == "UNKNOWN"
    assert result["nutrients"]["sugar"]["rating"] == "unknown"


def test_unknown_serving_is_flagged_as_assumed():
    result = analyze_nutrition({"sugar": 3}, serving_size="1 pack")
    assert result["basis_assumed"] is True
    assert result["nutrients"]["sugar"]["per_100"] == 3.0


def test_protein_uses_energy_share():
    # 25 g protein in 400 kcal = 25% of energy -> HIGH
    result = analyze_nutrition({"protein": 25, "calories": 400}, serving_size="100 g")
    assert result["nutrients"]["protein"]["level"] == "HIGH"


# ---------------- ingredient analysis ----------------

def test_split_ignores_commas_in_brackets():
    text = "WHEAT FLOUR, CHOCOLATE (SUGAR, COCOA), SALT."
    assert split_ingredients(text) == [
        "WHEAT FLOUR", "CHOCOLATE (SUGAR, COCOA)", "SALT"
    ]


def test_flags_and_allergens():
    text = (
        "Refined Wheat Flour (Maida), Sugar, Palm Oil, Milk Solids, "
        "Emulsifier (Soy Lecithin), Cocoa Butter"
    )
    result = analyze_ingredients(text)
    types = {h["type"] for h in result["highlights"]}
    assert {"palm_oil", "added_sugar", "refined_flour", "additive"} <= types
    assert "Soy" in result["allergens"]
    assert "Milk" in result["allergens"]
    assert "Wheat / Gluten" in result["allergens"]
    # "Sugar" is the 2nd ingredient -> warning
    assert any("first three" in note for note in result["top_ingredient_notes"])


def test_cocoa_butter_is_not_milk():
    assert "Milk" not in analyze_ingredients("Cocoa Butter, Cocoa Solids")["allergens"]


def test_empty_ingredients():
    assert analyze_ingredients(None)["count"] == 0


def test_nested_lists_are_flattened():
    text = ("Cereal products (57%) (rice meal (38%), corn meal (19%)), "
            "seasoning (spices, sugar, acidity regulators (330, 296)), salt")
    names = flatten_ingredients(text)
    assert names == [
        "Cereal products (57%)", "rice meal (38%)", "corn meal (19%)",
        "seasoning", "spices", "sugar", "acidity regulators (330, 296)",
        "salt",
    ]
    # single phrase / code-only brackets are not expanded
    assert flatten_ingredients("Emulsifier (Soy Lecithin)") == ["Emulsifier (Soy Lecithin)"]

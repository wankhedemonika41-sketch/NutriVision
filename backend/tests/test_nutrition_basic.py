from app.analysis.nutrition_analyzer import (
    analyze_nutrient, calculate_percentage, classify_nutrient,
)


def test_percentage_of_reference_value():
    assert calculate_percentage(50, 100) == 50.0
    assert calculate_percentage(1, 3) == 33.33          # rounded to 2 places
    assert calculate_percentage(150, 100) == 150.0      # can go above 100 %


def test_percentage_with_missing_or_invalid_input_is_none():
    assert calculate_percentage(None, 100) is None
    assert calculate_percentage(10, None) is None
    assert calculate_percentage(10, 0) is None
    assert calculate_percentage(10, -5) is None


def test_classification_boundaries():
    assert classify_nutrient(None) == "UNKNOWN"
    assert classify_nutrient(0) == "LOW"
    assert classify_nutrient(19.99) == "LOW"
    assert classify_nutrient(20) == "MODERATE"
    assert classify_nutrient(39.99) == "MODERATE"
    assert classify_nutrient(40) == "HIGH"
    assert classify_nutrient(250) == "HIGH"


def test_analyze_nutrient_returns_all_fields():
    result = analyze_nutrient(30, 50, "g")
    assert result == {
        "value": 30,
        "reference_value": 50,
        "unit": "g",
        "percentage": 60.0,
        "level": "HIGH",
    }


def test_analyze_nutrient_with_missing_value_is_unknown():
    result = analyze_nutrient(None, 50, "g")
    assert result["percentage"] is None
    assert result["level"] == "UNKNOWN"
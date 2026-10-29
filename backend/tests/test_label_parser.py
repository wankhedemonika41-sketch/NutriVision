from app.services.label_parser import parse_label

LABEL = """INGREDIENTS: Refined wheat flour (maida) (65%), sugar, edible vegeta-
ble oil (palm), invert syrup, milk solids, emulsifler (322).
Contains permitted natural colour (150d).
ALLERGEN INFORMATION: Contains wheat, milk.
NUTRITION INFORMATION (Approx. values)
Per 100 g   Per serving (25 g)   %RDA*
Energy (kcal) 479 120 6%
Protein (g) 5.9 1.5 3%
Carbohydrate (g) 73.1 18.3 7%
 - Total Sugars (g) 32.5 8.1
 - Added Sugars (g) 31.0 7.8 15%
Total Fat (g) 18.5 4.6 7%
 - Saturated Fat (g) 9.4 2.4 11%
 - Trans Fat (g) 0 0
Dietary Fibre (g) 1.2 0.3
Sodium (mg) 114 29 1%
"""


def test_ingredients_are_cut_at_the_right_place():
    ing = parse_label(LABEL)["ingredients"]
    assert ing.startswith("Refined wheat flour")
    assert "vegetable oil" in ing          # broken word joined back
    assert "emulsifier" in ing             # OCR spelling fixed
    assert "NUTRITION" not in ing.upper()
    assert "wheat, milk" not in ing        # allergen text removed


def test_per_100g_column_is_used_not_per_serving():
    n = parse_label(LABEL)["nutrition"]
    assert n["calories"] == 479
    assert n["carbohydrates"] == 73.1
    assert n["sugar"] == 32.5              # total sugars, not added sugars
    assert n["saturated_fat"] == 9.4
    assert n["trans_fat"] == 0
    assert n["sodium"] == 114


def test_serving_size_and_basis_are_detected():
    p = parse_label(LABEL)
    assert p["basis"] == "100g"
    assert p["serving_size_g"] == 25


def test_serving_first_layout_picks_second_column():
    text = ("Per serving (30 g)  Per 100 g\nEnergy (kcal) 120 400\n"
            "Protein (g) 3 10\nTotal Fat (g) 6 20\nSodium (mg) 90 300")
    n = parse_label(text)["nutrition"]
    assert n["calories"] == 400
    assert n["protein"] == 10
    assert n["sodium"] == 300


def test_kj_and_kcal_on_one_line():
    n = parse_label("Per 100 g\nEnergy 2004 kJ / 479 kcal")["nutrition"]
    assert n["calories"] == 479


def test_only_kj_is_converted():
    n = parse_label("Per 100 g\nEnergy 2092 kJ")["nutrition"]
    assert n["calories"] == 500


def test_salt_is_converted_to_sodium():
    n = parse_label("Per 100 g\nSalt 2.5 g")["nutrition"]
    assert n["sodium"] == 1000


def test_sodium_in_grams_is_converted_to_mg():
    n = parse_label("Per 100 g\nSodium 0.4 g")["nutrition"]
    assert n["sodium"] == 400


def test_ocr_digit_slips_are_fixed():
    n = parse_label("Per 100 g\nProtein (g) 1O.5")["nutrition"]
    assert n["protein"] == 10.5


def test_comma_decimal():
    n = parse_label("Per 100 g\nTotal Fat 28,3 g")["nutrition"]
    assert n["total_fat"] == 28.3


def test_impossible_numbers_give_warnings():
    p = parse_label("Per 100 g\nEnergy (kcal) 1200\nCarbohydrate 80 g\nProtein 30 g\nFat 40 g")
    assert any("too high" in w for w in p["warnings"])
    assert any("more than 100 g" in w for w in p["warnings"])


def test_empty_text_does_not_crash():
    p = parse_label("")
    assert p["ingredients"] is None
    assert p["found_fields"] == []
    assert p["warnings"]
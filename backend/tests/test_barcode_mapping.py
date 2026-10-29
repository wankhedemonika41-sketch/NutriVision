from app.services.barcode_service import map_off_product


def test_off_units_are_converted():
    product, nutrition = map_off_product({
        "product_name": "Test",
        "brands": "BrandA,BrandB",
        "nutriments": {
            "energy_100g": 2092,            # kJ -> 500 kcal
            "sodium_100g": 0.5,             # g -> 500 mg
            "sugars_100g": 10,
        },
    })
    assert nutrition["calories"] == 500.0
    assert nutrition["sodium"] == 500.0
    assert product["brand"] == "BrandA"


def test_salt_is_converted_to_sodium():
    _, nutrition = map_off_product({"nutriments": {"salt_100g": 2.5}})
    assert nutrition["sodium"] == 1000.0
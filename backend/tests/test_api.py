from unittest.mock import patch

from app.services.open_food_facts_service import OpenFoodFactsError


def _make_product(client, **overrides):
    payload = {
        "product_name": "Test Biscuit",
        "brand": "TESTCO",
        "category": "BISCUIT",
        "serving_size": "100 g",
        "ingredients": "Wheat Flour, Sugar, Palm Oil, Salt",
    }
    payload.update(overrides)
    response = client.post("/products/", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_root_and_database(client):
    assert client.get("/").json()["status"] == "running"
    assert client.get("/database-test").json()["database"] == "connected"


def test_reference_values_are_seeded(client):
    refs = client.get("/reference-values/").json()
    names = {r["nutrient"] for r in refs}
    assert {"sugar", "sodium", "calories"} <= names


def test_create_reference_value_endpoint_works(client):
    # was crashing before (daily_value bug)
    response = client.post("/reference-values/", json={
        "nutrient": "Potassium", "reference_value": 4700,
        "unit": "mg", "basis": "per day",
    })
    assert response.status_code == 200
    assert response.json()["nutrient"] == "potassium"


def test_product_nutrition_and_details(client):
    product = _make_product(client)
    nutrition = client.post("/nutrition/", json={
        "product_id": product["id"], "calories": 480, "sugar": 30,
        "total_fat": 20, "saturated_fat": 9, "sodium": 700, "fiber": 2,
        "protein": 6, "carbohydrates": 65, "trans_fat": 0,
    })
    assert nutrition.status_code == 200

    details = client.get(f"/products/details/{product['id']}").json()
    assert details["product"]["product_name"] == "Test Biscuit"
    assert details["analysis"]["basis"] == "per 100 g"
    assert details["analysis"]["nutrients"]["sugar"]["rating"] == "limit"
    assert details["analysis"]["nutrients"]["sugar"]["percent_daily_value"] == 60.0
    assert any(h["type"] == "palm_oil"
               for h in details["ingredient_analysis"]["highlights"])

    # second nutrition record is rejected
    again = client.post("/nutrition/", json={"product_id": product["id"]})
    assert again.status_code == 400

    # old analysis endpoint still works
    old = client.get(f"/analysis/nutrition/{product['id']}")
    assert old.status_code == 200
    assert old.json()["analysis"]["summary"]["limit"]


def test_details_without_nutrition(client):
    product = _make_product(client, product_name="No Nutrition Item")
    details = client.get(f"/products/details/{product['id']}").json()
    assert details["nutrition"] is None
    assert details["analysis"] is None


def test_search_by_name_and_brand_with_pagination(client):
    _make_product(client, product_name="Searchable Chips", brand="CRUNCHY")
    by_name = client.get("/products/search", params={"q": "searchable"}).json()
    by_brand = client.get("/products/search", params={"q": "crunchy"}).json()
    assert any(p["product_name"] == "Searchable Chips" for p in by_name)
    assert any(p["product_name"] == "Searchable Chips" for p in by_brand)

    # % typed by the user is literal, not a wildcard
    assert client.get("/products/search", params={"q": "%"}).json() == []

    page = client.get("/products/", params={"limit": 1}).json()
    assert len(page) == 1


def test_duplicate_barcode_returns_409(client):
    _make_product(client, product_name="Barcode One", barcode="8901234567890")
    response = client.post("/products/", json={
        "product_name": "Barcode Two", "barcode": "8901234567890"})
    assert response.status_code == 409


def test_404s(client):
    assert client.get("/products/999999").status_code == 404
    assert client.get("/products/details/999999").status_code == 404


def test_scan_local_barcode(client):
    _make_product(client, product_name="Scan Local", barcode="8900000000011")
    data = client.get("/scan/8900000000011").json()
    assert data["source"] == "NutriVision database"
    assert data["product"]["product_name"] == "Scan Local"


def test_scan_rejects_bad_barcode(client):
    assert client.get("/scan/abc").status_code == 422


OFF_SAMPLE = {
    "status": 1,
    "product": {
        "product_name": "Mock Chips", "brands": "MockBrand, Other",
        "categories": "Snacks, Chips", "ingredients_text": "Potato, Palm Oil, Salt",
        "nutriments": {
            "energy-kcal_100g": 520, "fat_100g": 30, "saturated-fat_100g": 14,
            "sugars_100g": 1, "salt_100g": 1.5, "proteins_100g": 6,
            "carbohydrates_100g": 50, "fiber_100g": 4,
        },
    },
}


def test_scan_falls_back_to_open_food_facts(client):
    target = "app.routes.scan_routes.get_product_from_open_food_facts"
    with patch(target, return_value=OFF_SAMPLE):
        data = client.get("/scan/5000000000017").json()
    assert data["source"] == "Open Food Facts"
    assert data["product"]["brand"] == "MockBrand"
    assert data["nutrition"]["sodium"] == 600.0       # 1.5 g salt -> 600 mg sodium
    assert data["analysis"]["nutrients"]["saturated_fat"]["rating"] == "limit"


def test_scan_not_found_and_upstream_error(client):
    target = "app.routes.scan_routes.get_product_from_open_food_facts"
    with patch(target, return_value=None):
        assert client.get("/scan/5000000000024").status_code == 404
    with patch(target, side_effect=OpenFoodFactsError("down")):
        assert client.get("/scan/5000000000031").status_code == 502


def test_admin_key_protects_writes(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    denied = client.post("/products/", json={"product_name": "Blocked"})
    assert denied.status_code == 401
    allowed = client.post(
        "/products/", json={"product_name": "Allowed"},
        headers={"X-API-Key": "secret123"})
    assert allowed.status_code == 200
    # reads stay open
    assert client.get("/products/").status_code == 200

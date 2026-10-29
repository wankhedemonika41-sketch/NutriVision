import requests

OFF_URL = "https://world.openfoodfacts.org/api/v2/product"
OFF_FIELDS = ",".join([
    "product_name", "product_name_en", "generic_name", "brands",
    "categories", "categories_tags", "ingredients_text",
    "ingredients_text_en", "nutriments", "serving_size",
    "image_front_small_url",
])
HEADERS = {"User-Agent": "NutriVision/1.0 (college-project)"}


def fetch_off_product(barcode):
    """Open Food Facts v2: status 1 = found, 0 = not found."""
    response = requests.get(
        f"{OFF_URL}/{barcode}.json",
        params={"fields": OFF_FIELDS},
        headers=HEADERS,
        timeout=10,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    data = response.json()

    if data.get("status") != 1 or not data.get("product"):
        return None

    return data["product"]


def _num(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mg(grams):
    return None if grams is None else round(grams * 1000, 1)


def map_off_product(off):
    """Open Food Facts product -> (product dict, nutrition dict per 100 g)."""
    n = off.get("nutriments") or {}

    calories = _num(n.get("energy-kcal_100g"))
    if calories is None:
        kj = _num(n.get("energy_100g"))          # OFF energy is in kJ
        calories = None if kj is None else round(kj / 4.184, 1)

    sodium_g = _num(n.get("sodium_100g"))        # OFF sodium is in grams
    if sodium_g is None:
        salt_g = _num(n.get("salt_100g"))
        sodium_g = None if salt_g is None else salt_g / 2.5

    nutrition = {
        "calories": calories,
        "carbohydrates": _num(n.get("carbohydrates_100g")),
        "protein": _num(n.get("proteins_100g")),
        "total_fat": _num(n.get("fat_100g")),
        "saturated_fat": _num(n.get("saturated-fat_100g")),
        "trans_fat": _num(n.get("trans-fat_100g")),
        "sugar": _num(n.get("sugars_100g")),
        "sodium": _mg(sodium_g),
        "fiber": _num(n.get("fiber_100g")),
        "cholesterol": _mg(_num(n.get("cholesterol_100g"))),
    }

    tags = " ".join(off.get("categories_tags") or []).lower()
    if any(word in tags for word in ("beverage", "drink", "juice")):
        category = "BEVERAGE"
    else:
        first = (off.get("categories") or "").split(",")[0].strip()
        category = first or None

    product = {
        "product_name": (off.get("product_name_en") or off.get("product_name")
                         or off.get("generic_name") or "Unnamed product"),
        "brand": (off.get("brands") or "").split(",")[0].strip() or None,
        "category": category,
        "ingredients": off.get("ingredients_text_en") or off.get("ingredients_text"),
        "serving_size": off.get("serving_size"),
        "image_url": off.get("image_front_small_url"),
    }

    return product, nutrition
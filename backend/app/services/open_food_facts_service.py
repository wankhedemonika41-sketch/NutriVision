import requests


OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v3/product"


def get_product_from_open_food_facts(barcode: str):
    url = f"{OPEN_FOOD_FACTS_URL}/{barcode}"

    headers = {
        "User-Agent": "NutriVision/1.0 (college-project)"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    data = response.json()

    if data.get("status") != 1:
        return None

    return data
import uuid

from app.database.connection import SessionLocal
from app.models.nutrition import Nutrition
from app.models.product import Product
from app.services.recommendation_service import diet_problem, recommend


# ====================== pure logic ======================

def _p(pid, name, score, per100=None, ingredients="Rolled oats, jaggery",
       allergens=None, sweetener=False, grade=None, price=50):
    return {
        "id": pid, "product_name": name, "brand": "B", "category": "SNACKS",
        "price_inr": price, "ingredients": ingredients,
        "allergens": allergens or [],
        "per_100g": per100 or {},
        "highlights": [{"type": "sweetener", "label": "Sweetener", "severity": "info"}] if sweetener else [],
        "health": {"available": True, "score": score,
                   "grade": grade or ("A" if score >= 75 else "C")},
    }


TARGET = _p(1, "Original", 30, {"sugar": 40, "sodium": 300, "calories": 500, "protein": 5})
NOBODY = {"diet": None, "allergies": [], "goal": None}


def _names(result):
    return [r["product_name"] for r in result["recommendations"]]


def test_only_clearly_healthier_products_are_suggested_best_first():
    candidates = [
        _p(2, "Much better", 70), _p(3, "Best", 85), _p(4, "Slightly better", 35),
        _p(5, "Worse", 20),
    ]
    result = recommend(TARGET, candidates, NOBODY)
    assert _names(result) == ["Best", "Much better"]          # +5 is below the 8 point bar
    assert result["recommendations"][0]["score_gain"] == 55


def test_the_product_itself_and_same_name_packs_are_never_suggested():
    candidates = [_p(1, "Original", 90), _p(9, "  original ", 90), _p(2, "Other", 90)]
    assert _names(recommend(TARGET, candidates, NOBODY)) == ["Other"]


def test_a_healthy_product_needs_no_alternatives():
    healthy = _p(1, "Oats", 88)
    result = recommend(healthy, [_p(2, "Even better", 99)], NOBODY)
    assert result["recommendations"] == []
    assert "already a healthy choice" in result["message"]


def test_no_score_means_no_suggestions():
    broken = dict(TARGET, health={"available": False})
    result = recommend(broken, [_p(2, "X", 90)], NOBODY)
    assert result["recommendations"] == [] and "could not be calculated" in result["message"]


def test_allergens_are_filtered_and_explained():
    candidates = [_p(2, "Has nuts", 80, allergens=["Tree nuts"]), _p(3, "Safe", 70)]
    result = recommend(TARGET, candidates, {**NOBODY, "allergies": ["Tree nuts"]})
    assert _names(result) == ["Safe"]
    assert result["excluded"]["allergen"] == 1
    assert "Tree nuts" in result["notes"][0]


def test_products_with_unknown_ingredients_are_dropped_when_allergies_are_set():
    candidates = [_p(2, "Mystery", 80, ingredients=None), _p(3, "Known", 70)]
    with_allergy = recommend(TARGET, candidates, {**NOBODY, "allergies": ["Milk"]})
    assert _names(with_allergy) == ["Known"]
    assert with_allergy["excluded"]["unknown_ingredients"] == 1
    without = recommend(TARGET, candidates, NOBODY)
    assert set(_names(without)) == {"Mystery", "Known"}        # nothing to protect against


def test_diet_rules():
    assert diet_problem("vegetarian", "Chicken extract, salt", []) == "contains meat, fish or gelatin"
    assert diet_problem("vegetarian", "Sugar, gelatin", []) == "contains meat, fish or gelatin"
    assert diet_problem("vegetarian", "Wheat, egg powder", ["Egg"]) == "contains egg"
    assert diet_problem("vegetarian", "Milk solids, sugar", ["Milk"]) is None
    assert diet_problem("eggetarian", "Wheat, egg powder", ["Egg"]) is None
    assert diet_problem("eggetarian", "Tuna, salt", []) == "contains meat, fish or gelatin"
    assert diet_problem("vegan", "Milk solids, sugar", ["Milk"]) == "contains milk"
    assert diet_problem("vegan", "Oats, honey", []) == "contains honey"
    assert diet_problem("vegan", "Oats, jaggery", []) is None
    assert diet_problem("non_vegetarian", "Chicken", []) is None
    assert diet_problem(None, "Chicken", []) is None
    assert diet_problem("vegan", "", []) == "unknown"
    assert diet_problem("vegetarian", None, []) == "unknown"


def test_diet_is_applied_to_suggestions():
    candidates = [
        _p(2, "Chicken chips", 80, ingredients="Potato, chicken powder"),
        _p(3, "Veg chips", 70, ingredients="Potato, salt"),
    ]
    result = recommend(TARGET, candidates, {**NOBODY, "diet": "vegetarian"})
    assert _names(result) == ["Veg chips"]
    assert result["excluded"]["diet"] == 1
    assert "estimated" in result["notes"][0]


def test_goal_moves_a_matching_product_up():
    low_sugar = _p(2, "Low sugar", 60, {"sugar": 2, "sodium": 300, "calories": 500, "protein": 5})
    higher_score = _p(3, "Higher score", 66, {"sugar": 39, "sodium": 100, "calories": 500, "protein": 5})
    plain = recommend(TARGET, [low_sugar, higher_score], NOBODY)
    goal = recommend(TARGET, [low_sugar, higher_score], {**NOBODY, "goal": "manage_sugar"})
    assert _names(plain)[0] == "Higher score"
    assert _names(goal)[0] == "Low sugar"
    assert goal["recommendations"][0]["goal_match"].startswith("Fits your goal: Sugar is")
    assert plain["recommendations"][0]["goal_match"] is None


def test_sweetener_products_are_tagged_and_ranked_slightly_lower():
    sweet = _p(2, "Diet one", 72, sweetener=True)
    plain = _p(3, "Plain one", 70)
    result = recommend(TARGET, [sweet, plain], NOBODY)
    assert _names(result) == ["Plain one", "Diet one"]
    assert result["recommendations"][1]["contains_sweetener"] is True
    sugar_goal = recommend(TARGET, [sweet, plain], {**NOBODY, "goal": "manage_sugar"})
    assert _names(sugar_goal)[0] == "Diet one"                  # no penalty for a sugar goal


def test_trivial_differences_are_not_listed_as_reasons():
    cand = _p(2, "Better", 80, {"sugar": 8, "sodium": 300, "calories": 500, "trans_fat": 0, "protein": 5})
    target = dict(TARGET, per_100g={"sugar": 40, "sodium": 300, "calories": 500, "trans_fat": 0.1, "protein": 5})
    reasons = recommend(target, [cand], NOBODY)["recommendations"][0]["reasons"]
    assert reasons == ["Sugar is 80% lower (8 vs 40 g per 100 g)"]


def test_limit_is_respected():
    candidates = [_p(i, f"P{i}", 60 + i) for i in range(2, 12)]
    assert len(recommend(TARGET, candidates, NOBODY, limit=3)["recommendations"]) == 3


def test_empty_results_explain_themselves():
    few = recommend(TARGET, [_p(2, "Only one", 31)], NOBODY)
    assert "very few similar products" in few["message"]
    many = recommend(TARGET, [_p(i, f"P{i}", 32) for i in range(2, 8)], NOBODY)
    assert "No clearly healthier alternatives" in many["message"]
    blocked = recommend(TARGET, [_p(2, "Nutty", 80, allergens=["Tree nuts"])],
                        {**NOBODY, "allergies": ["Tree nuts"]})
    assert "do not match your allergies" in blocked["message"]


# ====================== through the real API ======================

JUNK = dict(calories=520, carbohydrates=65, protein=5, total_fat=26,
            saturated_fat=12, trans_fat=0, sugar=40, sodium=250, fiber=0, cholesterol=0)
GOOD = dict(calories=360, carbohydrates=55, protein=12, total_fat=6,
            saturated_fat=1, trans_fat=0, sugar=5, sodium=60, fiber=10, cholesterol=0)
GREAT = dict(calories=300, carbohydrates=50, protein=14, total_fat=4,
             saturated_fat=0.5, trans_fat=0, sugar=1, sodium=20, fiber=12, cholesterol=0)

JUNK_TEXT = "Sugar, palm oil, refined wheat flour, milk solids, emulsifier, artificial flavour"
GOOD_TEXT = "Rolled oats, jaggery, sunflower oil"
NUTTY_TEXT = "Rolled oats, almonds, jaggery"


def _seed(category, sub, rows):
    db = SessionLocal()
    ids = []
    for name, text, nutrition in rows:
        product = Product(product_name=name, brand="B", category=category,
                          sub_category=sub, serving_size="100",
                          ingredients=text, price_inr=60)
        product.nutrition = Nutrition(**nutrition)
        db.add(product)
        db.commit()
        ids.append(product.id)
    db.close()
    return ids


def _user(client, **profile):
    email = f"r-{uuid.uuid4().hex[:10]}@example.com"
    token = client.post("/auth/register", json={
        "name": "Rec Tester", "email": email, "password": "Passw0rdOK"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    if profile:
        assert client.put("/profile", headers=headers, json=profile).status_code == 200
    return headers


def _tag():
    return uuid.uuid4().hex[:8].upper()


def test_recommendations_need_login_and_a_real_product(client):
    assert client.get("/recommendations/1").status_code == 401
    assert client.get("/recommendations/999999", headers=_user(client)).status_code == 404


def test_similar_products_in_the_same_sub_category_are_preferred(client):
    cat = f"CAT{_tag()}"
    target, *siblings = _seed(cat, "BARS", [("Junk bar", JUNK_TEXT, JUNK)] +
                              [(f"Good bar {i}", GOOD_TEXT, GOOD) for i in range(5)])
    other = _seed(cat, "DRINKS", [("Good drink", GOOD_TEXT, GOOD)])[0]

    d = client.get(f"/recommendations/{target}", headers=_user(client)).json()
    ids = {r["id"] for r in d["recommendations"]}
    assert ids and ids <= set(siblings)
    assert other not in ids
    assert "similar products (Bars)" in d["compared_with"]
    assert d["profile_used"]["personalised"] is False


def test_small_sub_category_falls_back_to_the_whole_category(client):
    cat = f"CAT{_tag()}"
    target = _seed(cat, "RARE", [("Junk rare", JUNK_TEXT, JUNK)])[0]
    good = _seed(cat, "COMMON", [(f"Good {i}", GOOD_TEXT, GOOD) for i in range(3)])

    d = client.get(f"/recommendations/{target}", headers=_user(client)).json()
    assert {r["id"] for r in d["recommendations"]} <= set(good) and d["recommendations"]
    assert "products in" in d["compared_with"]


def test_allergies_and_diet_from_the_profile_are_respected(client):
    cat = f"CAT{_tag()}"
    target, nutty, safe = _seed(cat, "BARS", [
        ("Junk", JUNK_TEXT, JUNK),
        ("Nutty good", NUTTY_TEXT, GOOD),
        ("Safe good", GOOD_TEXT, GOOD),
    ])
    _seed(cat, "BARS", [(f"Filler {i}", GOOD_TEXT, GOOD) for i in range(4)])

    headers = _user(client, allergies=["Tree nuts"], diet_preference="vegan")
    d = client.get(f"/recommendations/{target}", headers=headers).json()
    ids = {r["id"] for r in d["recommendations"]}
    assert nutty not in ids and safe in ids
    assert d["excluded"]["allergen"] == 1
    assert d["profile_used"]["personalised"] is True
    assert d["profile_used"]["allergies"] == ["Tree nuts"]


def test_a_healthy_product_gets_no_suggestions_through_the_api(client):
    cat = f"CAT{_tag()}"
    target = _seed(cat, "BARS", [("Oat bar", "Rolled oats", GREAT)])[0]
    d = client.get(f"/recommendations/{target}", headers=_user(client)).json()
    assert d["product"]["score"] >= 75                      # precondition of this test
    assert d["recommendations"] == []
    assert "already a healthy choice" in d["message"]
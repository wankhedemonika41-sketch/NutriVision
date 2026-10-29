import uuid

import pytest

from app.services.profile_service import compute_bmi


def _login(client):
    email = f"p-{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/auth/register", json={
        "name": "Profile Tester", "email": email, "password": "Passw0rdOK"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


FULL = {
    "age": 24, "gender": "female", "height_cm": 160, "weight_kg": 58,
    "diet_preference": "vegetarian", "allergies": ["Milk", "Soy"],
    "health_goal": "manage_sugar",
}


# ---------------- BMI ----------------

def test_bmi_value_and_category():
    bmi = compute_bmi(160, 58, 24)
    assert bmi["value"] == 22.7
    assert bmi["category"] == "Healthy weight"


@pytest.mark.parametrize("weight, category", [
    (18.4, "Underweight"),
    (18.5, "Healthy weight"),
    (22.9, "Healthy weight"),
    (23.0, "Overweight"),
    (24.9, "Overweight"),
    (25.0, "Obese"),
    (40.0, "Obese"),
])
def test_bmi_uses_asian_indian_cut_offs(weight, category):
    # height 100 cm makes BMI equal to the weight, so the boundaries are exact
    assert compute_bmi(100, weight, 30)["category"] == category


def test_bmi_has_no_category_for_children_and_teenagers():
    bmi = compute_bmi(150, 40, 14)
    assert bmi["value"] == 17.8
    assert bmi["category"] is None
    assert "growth charts" in bmi["note"]


def test_bmi_needs_height_and_weight():
    assert compute_bmi(None, 60)["value"] is None
    assert compute_bmi(160, None)["value"] is None
    assert compute_bmi(0, 60)["value"] is None


# ---------------- /profile ----------------

def test_profile_needs_login(client):
    assert client.get("/profile").status_code == 401
    assert client.put("/profile", json=FULL).status_code == 401


def test_options_are_public_and_complete(client):
    options = client.get("/profile/options").json()
    assert "Milk" in options["allergens"] and "Wheat / Gluten" in options["allergens"]
    assert {d["value"] for d in options["diets"]} >= {"vegetarian", "vegan", "eggetarian"}
    assert any(g["value"] == "manage_sugar" for g in options["goals"])


def test_new_user_has_an_empty_profile(client):
    data = client.get("/profile", headers=_login(client)).json()
    assert data["profile"]["allergies"] == []
    assert data["profile"]["age"] is None
    assert data["bmi"]["value"] is None


def test_profile_is_saved_and_read_back(client):
    headers = _login(client)
    saved = client.put("/profile", headers=headers, json=FULL)
    assert saved.status_code == 200
    assert saved.json()["bmi"]["category"] == "Healthy weight"

    again = client.get("/profile", headers=headers).json()
    assert again["profile"] == FULL


def test_saving_again_replaces_the_whole_profile(client):
    headers = _login(client)
    client.put("/profile", headers=headers, json=FULL)
    client.put("/profile", headers=headers, json={"age": 30})
    profile = client.get("/profile", headers=headers).json()["profile"]
    assert profile["age"] == 30
    assert profile["allergies"] == []
    assert profile["diet_preference"] is None


def test_duplicate_allergies_are_merged(client):
    headers = _login(client)
    r = client.put("/profile", headers=headers, json={"allergies": ["Milk", "Soy", "Milk"]})
    assert r.json()["profile"]["allergies"] == ["Milk", "Soy"]


def test_profiles_are_private_to_each_user(client):
    alice, bob = _login(client), _login(client)
    client.put("/profile", headers=alice, json=FULL)
    assert client.get("/profile", headers=bob).json()["profile"]["allergies"] == []


@pytest.mark.parametrize("change", [
    {"age": 3}, {"age": 200},
    {"height_cm": 20}, {"height_cm": 400},
    {"weight_kg": 2}, {"weight_kg": 900},
    {"allergies": ["Pollen"]},
    {"diet_preference": "carnivore"},
    {"health_goal": "get_famous"},
    {"gender": "robot"},
])
def test_impossible_values_are_rejected(client, change):
    r = client.put("/profile", headers=_login(client), json={**FULL, **change})
    assert r.status_code == 422
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.database.connection import SessionLocal
from app.models.nutrition import Nutrition
from app.models.product import Product
from app.models.scan_history import ScanHistory
from app.routes import history_routes
from app.services.history_service import summarize

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)      # a Saturday


def _e(days_ago, score, grade, **extra):
    base = {
        "created_at": NOW - timedelta(days=days_ago),
        "score": score, "grade": grade, "category": "SNACKS",
        "product_name": f"P{days_ago}-{score}", "product_id": None,
        "barcode": None, "cautions": [],
        "calories": None, "sugar": None, "sodium": None, "saturated_fat": None,
    }
    base.update(extra)
    return base


# ====================== report maths ======================

def test_empty_history_gives_an_empty_report():
    r = summarize([], 7, NOW)
    assert r["total"] == 0 and r["average_score"] is None
    assert r["healthy_share"] is None and r["insights"] == []
    assert len(r["daily"]) == 7 and all(d["count"] == 0 for d in r["daily"])
    assert r["best"] is None and r["worst"] is None


def test_totals_average_grades_and_best_worst():
    entries = [_e(0, 80, "A"), _e(1, 60, "B"), _e(2, 20, "D"), _e(2, 40, "C")]
    r = summarize(entries, 7, NOW)
    assert r["total"] == 4
    assert r["average_score"] == 50.0
    assert r["grades"] == {"A": 1, "B": 1, "C": 1, "D": 1}
    assert r["healthy_share"] == 50
    assert r["best"]["score"] == 80 and r["worst"]["score"] == 20


def test_only_entries_inside_the_period_count():
    entries = [_e(0, 80, "A"), _e(6, 70, "A"), _e(7, 10, "D"), _e(30, 10, "D")]
    r = summarize(entries, 7, NOW)
    assert r["total"] == 2                 # days 0..6 are inside a 7 day report
    assert r["period"] == {"start": "2026-10-18", "end": "2026-10-24"}


def test_daily_points_cover_every_day_and_average_per_day():
    r = summarize([_e(0, 80, "A"), _e(0, 60, "B"), _e(2, 30, "D")], 7, NOW)
    by_date = {d["date"]: d for d in r["daily"]}
    assert by_date["2026-10-24"] == {"date": "2026-10-24", "count": 2, "average": 70.0}
    assert by_date["2026-10-22"]["count"] == 1
    assert by_date["2026-10-23"] == {"date": "2026-10-23", "count": 0, "average": None}
    assert [d["date"] for d in r["daily"]] == sorted(d["date"] for d in r["daily"])


def test_change_compares_with_the_previous_period():
    now_entries = [_e(1, 70, "B"), _e(2, 70, "B")]
    before = [_e(8, 40, "C"), _e(10, 40, "C")]
    r = summarize(now_entries + before, 7, NOW)
    assert r["previous"] == {"total": 2, "average_score": 40.0}
    assert r["change"] == 30.0
    assert any("30 points higher" in note for note in r["insights"])


def test_no_change_figure_without_a_previous_period():
    r = summarize([_e(1, 70, "B")], 7, NOW)
    assert r["change"] is None


def test_a_small_change_is_called_about_the_same():
    r = summarize([_e(1, 50, "C"), _e(9, 48, "C")], 7, NOW)
    assert any("about the same" in note for note in r["insights"])


def test_most_common_concern_and_categories():
    entries = [
        _e(0, 30, "D", cautions=["Added sugar", "Palm oil"], category="BISCUIT"),
        _e(1, 35, "C", cautions=["Added sugar"], category="BISCUIT"),
        _e(2, 90, "A", cautions=[], category="JUICE"),
    ]
    r = summarize(entries, 7, NOW)
    assert r["top_cautions"][0] == {"label": "Added sugar", "count": 2}
    assert r["categories"][0] == {"category": "BISCUIT", "count": 2, "average": 32.5}
    assert any("Added sugar (in 2 of 3 products)" in note for note in r["insights"])


def test_unique_products_are_counted_once():
    entries = [
        _e(0, 50, "C", product_id=7), _e(1, 50, "C", product_id=7),
        _e(2, 40, "C", barcode="3017620422003"), _e(3, 40, "C", barcode="3017620422003"),
        _e(4, 40, "C", product_name="Label A"), _e(5, 40, "C", product_name="label a "),
    ]
    assert summarize(entries, 7, NOW)["unique_products"] == 3


def test_averages_ignore_missing_values():
    entries = [_e(0, 50, "C", sugar=10), _e(1, 50, "C", sugar=20), _e(2, 50, "C")]
    assert summarize(entries, 7, NOW)["averages"]["sugar"] == 15.0
    assert summarize(entries, 7, NOW)["averages"]["sodium"] is None


def test_a_day_follows_the_users_own_clock():
    # 21:00 UTC on the 23rd is already the 24th in India (UTC+5:30)
    late = NOW.replace(hour=21) - timedelta(days=1)
    entries = [_e(0, 50, "C", created_at=late)]
    utc_view = summarize(entries, 3, NOW, 0)
    india_view = summarize(entries, 3, NOW, 330)
    assert [d["count"] for d in utc_view["daily"]] == [0, 1, 0]       # 22nd, 23rd, 24th
    assert [d["count"] for d in india_view["daily"]] == [0, 0, 1]


def test_naive_datetimes_from_sqlite_are_treated_as_utc():
    naive = _e(0, 50, "C", created_at=NOW.replace(tzinfo=None))
    assert summarize([naive], 7, NOW)["total"] == 1


def test_mostly_unhealthy_history_gets_a_hint():
    r = summarize([_e(0, 20, "D"), _e(1, 30, "D"), _e(2, 80, "A")], 7, NOW)
    assert any("Only 33% of the products" in note for note in r["insights"])


# ====================== through the real API ======================

def _headers(client):
    email = f"h-{uuid.uuid4().hex[:10]}@example.com"
    token = client.post("/auth/register", json={
        "name": "History Tester", "email": email, "password": "Passw0rdOK"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _product(name="History product", text="Sugar, palm oil, refined wheat flour, emulsifier"):
    db = SessionLocal()
    product = Product(product_name=name, brand="B", category=f"H{uuid.uuid4().hex[:6]}",
                      serving_size="100", ingredients=text, price_inr=40)
    product.nutrition = Nutrition(calories=500, carbohydrates=60, protein=5, total_fat=24,
                                  saturated_fat=11, trans_fat=0, sugar=35, sodium=300,
                                  fiber=1, cholesterol=0)
    db.add(product)
    db.commit()
    pid = product.id
    db.close()
    return pid


def _snapshot(**extra):
    base = {"source": "barcode", "barcode": "3017620422003", "product_name": "Nutella",
            "brand": "Ferrero", "category": "Spreads", "score": 31.0, "grade": "D",
            "sugar": 56.3, "sodium": 42.8, "cautions": ["Added sugar", "Palm oil"]}
    base.update(extra)
    return base


def test_history_needs_login(client):
    assert client.post("/history", json=_snapshot()).status_code == 401
    assert client.get("/history").status_code == 401
    assert client.get("/history/summary").status_code == 401
    assert client.delete("/history").status_code == 401
    assert client.delete("/history/1").status_code == 401


def test_a_product_entry_is_scored_by_the_server(client):
    headers, pid = _headers(client), _product()
    r = client.post("/history", headers=headers, json={"source": "product", "product_id": pid})
    assert r.status_code == 201 and r.json()["duplicate"] is False

    official = client.get(f"/health-score/product/{pid}").json()
    item = client.get("/history", headers=headers).json()["items"][0]
    assert item["product_id"] == pid
    assert item["score"] == official["score"] and item["grade"] == official["grade"]
    assert "Added sugar" in item["cautions"]


def test_the_client_cannot_fake_the_score_of_a_database_product(client):
    headers, pid = _headers(client), _product()
    client.post("/history", headers=headers,
                json={"source": "product", "product_id": pid, "score": 99, "grade": "A"})
    item = client.get("/history", headers=headers).json()["items"][0]
    assert item["score"] != 99 and item["grade"] != "A"


def test_unknown_or_unscorable_products_are_rejected(client):
    headers = _headers(client)
    assert client.post("/history", headers=headers,
                       json={"source": "product", "product_id": 99999999}).status_code == 404
    db = SessionLocal()
    bare = Product(product_name="No nutrition", category="X")
    db.add(bare); db.commit(); bare_id = bare.id; db.close()
    assert client.post("/history", headers=headers,
                       json={"source": "product", "product_id": bare_id}).status_code == 422


def test_opening_the_same_product_again_is_not_logged_twice(client):
    headers, pid = _headers(client), _product()
    body = {"source": "product", "product_id": pid}
    first = client.post("/history", headers=headers, json=body)
    again = client.post("/history", headers=headers, json=body)
    assert first.status_code == 201 and again.status_code == 200
    assert again.json() == {"id": first.json()["id"], "duplicate": True}
    assert client.get("/history", headers=headers).json()["total"] == 1


def test_a_barcode_snapshot_is_stored_and_deduplicated(client):
    headers = _headers(client)
    assert client.post("/history", headers=headers, json=_snapshot()).status_code == 201
    assert client.post("/history", headers=headers, json=_snapshot()).json()["duplicate"] is True
    item = client.get("/history", headers=headers).json()["items"][0]
    assert item["barcode"] == "3017620422003" and item["cautions"] == ["Added sugar", "Palm oil"]


def test_label_scans_are_always_logged(client):
    headers = _headers(client)
    label = {"source": "label", "product_name": "Scanned label", "score": 42.5, "grade": "C"}
    client.post("/history", headers=headers, json=label)
    client.post("/history", headers=headers, json=label)
    assert client.get("/history", headers=headers).json()["total"] == 2


@pytest.mark.parametrize("change", [
    {"score": 101}, {"score": -1}, {"grade": "E"}, {"source": "other"},
    {"barcode": "12ab"}, {"sugar": -4}, {"product_name": ""},
])
def test_bad_snapshots_are_rejected(client, change):
    assert client.post("/history", headers=_headers(client),
                       json=_snapshot(**change)).status_code == 422


def test_each_source_needs_its_own_fields(client):
    headers = _headers(client)
    assert client.post("/history", headers=headers, json={"source": "product"}).status_code == 422
    assert client.post("/history", headers=headers,
                       json={"source": "barcode", "product_name": "X"}).status_code == 422


def test_list_is_newest_first_and_paged(client):
    headers = _headers(client)
    for i in range(5):
        client.post("/history", headers=headers, json={
            "source": "label", "product_name": f"Label {i}", "score": 10 + i, "grade": "D"})
    page = client.get("/history?limit=2&offset=0", headers=headers).json()
    assert page["total"] == 5
    assert [x["product_name"] for x in page["items"]] == ["Label 4", "Label 3"]
    nxt = client.get("/history?limit=2&offset=4", headers=headers).json()
    assert [x["product_name"] for x in nxt["items"]] == ["Label 0"]


def test_history_is_private_to_each_user(client):
    alice, bob = _headers(client), _headers(client)
    client.post("/history", headers=alice, json=_snapshot())
    assert client.get("/history", headers=bob).json() == {"total": 0, "items": []}
    assert client.get("/history/summary", headers=bob).json()["total"] == 0


def test_delete_one_entry_only_your_own(client):
    alice, bob = _headers(client), _headers(client)
    entry = client.post("/history", headers=alice, json=_snapshot()).json()["id"]
    assert client.delete(f"/history/{entry}", headers=bob).status_code == 404
    assert client.get("/history", headers=alice).json()["total"] == 1
    assert client.delete(f"/history/{entry}", headers=alice).status_code == 204
    assert client.get("/history", headers=alice).json()["total"] == 0
    assert client.delete(f"/history/{entry}", headers=alice).status_code == 404


def test_clear_history_removes_only_your_entries(client):
    alice, bob = _headers(client), _headers(client)
    for h in (alice, bob):
        client.post("/history", headers=h, json=_snapshot())
    assert client.delete("/history", headers=alice).json() == {"deleted": 1}
    assert client.get("/history", headers=alice).json()["total"] == 0
    assert client.get("/history", headers=bob).json()["total"] == 1


def test_history_is_trimmed_to_the_limit(client, monkeypatch):
    monkeypatch.setattr(history_routes, "MAX_ENTRIES", 3)
    headers = _headers(client)
    for i in range(5):
        client.post("/history", headers=headers, json={
            "source": "label", "product_name": f"L{i}", "score": 50, "grade": "C"})
    page = client.get("/history", headers=headers).json()
    assert page["total"] == 3
    assert [x["product_name"] for x in page["items"]] == ["L4", "L3", "L2"]


def test_summary_through_the_api_with_older_entries(client):
    headers = _headers(client)
    me = client.get("/auth/me", headers=headers).json()["id"]
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    for days_ago, score, grade in [(1, 70, "B"), (2, 20, "D"), (9, 40, "C")]:
        db.add(ScanHistory(user_id=me, source="label", created_at=now - timedelta(days=days_ago),
                           product_name=f"old-{days_ago}", score=score, grade=grade,
                           category="SNACKS", cautions="Added sugar"))
    db.commit(); db.close()

    r = client.get("/history/summary?days=7&tz_offset=330", headers=headers).json()
    assert r["total"] == 2 and r["average_score"] == 45.0
    assert r["previous"]["total"] == 1 and r["change"] == 5.0
    assert r["top_cautions"][0] == {"label": "Added sugar", "count": 2}
    assert len(r["daily"]) == 7

    month = client.get("/history/summary?days=30", headers=headers).json()
    assert month["total"] == 3 and len(month["daily"]) == 30


@pytest.mark.parametrize("query", ["days=0", "days=400", "tz_offset=9999", "days=abc"])
def test_summary_rejects_silly_parameters(client, query):
    assert client.get(f"/history/summary?{query}", headers=_headers(client)).status_code == 422
import uuid

import pytest

from app.services import auth_service
from app.services.auth_service import (
    create_token, hash_password, read_token, reset_throttle, verify_password,
)


@pytest.fixture(autouse=True)
def _fresh_throttle():
    reset_throttle()
    yield
    reset_throttle()


def _email():
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


def _register(client, email=None, password="Passw0rdOK", name="Asha Patil"):
    return client.post("/auth/register", json={
        "name": name,
        "email": _email() if email is None else email,
        "password": password})


# ---------------- password hashing ----------------

def test_password_hash_is_salted_and_verifies():
    a, b = hash_password("Secret123"), hash_password("Secret123")
    assert a != b                                   # random salt
    assert verify_password("Secret123", a)
    assert not verify_password("secret123", a)
    assert "Secret123" not in a


def test_broken_hash_never_verifies():
    assert not verify_password("x", "garbage")
    assert not verify_password("x", "")


# ---------------- tokens ----------------

def test_token_round_trip():
    assert read_token(create_token(42)) == 42


def test_tampered_or_random_token_is_rejected():
    token = create_token(1)
    assert read_token(token + "x") is None
    assert read_token("not-a-token") is None
    assert read_token("") is None


def test_expired_token_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_EXPIRE_DAYS", "1")
    import jwt
    from datetime import datetime, timedelta, timezone
    old = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(seconds=5)},
        auth_service._secret, algorithm="HS256")
    assert read_token(old) is None


# ---------------- register ----------------

def test_register_returns_token_and_user_without_password(client):
    r = _register(client, email="  New.User@Example.COM ")
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "new.user@example.com"
    assert body["user"]["name"] == "Asha Patil"
    assert "password" not in str(body).lower().replace("password_hash", "")
    assert "password_hash" not in body["user"]
    assert read_token(body["token"]) == body["user"]["id"]


def test_duplicate_email_is_rejected_even_with_different_case(client):
    email = _email()
    assert _register(client, email=email).status_code == 201
    r = _register(client, email=email.upper())
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


@pytest.mark.parametrize("password", ["short1", "onlyletters", "12345678"])
def test_weak_password_is_rejected(client, password):
    assert _register(client, password=password).status_code == 422


@pytest.mark.parametrize("email", ["nope", "a@b", "a b@c.com", ""])
def test_bad_email_is_rejected(client, email):
    assert _register(client, email=email).status_code == 422


def test_short_name_is_rejected(client):
    assert _register(client, name="A").status_code == 422


# ---------------- login ----------------

def test_login_works_with_right_password(client):
    email = _email()
    _register(client, email=email)
    r = client.post("/auth/login", json={"email": email.upper(), "password": "Passw0rdOK"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == email


def test_wrong_password_and_unknown_email_give_the_same_error(client):
    email = _email()
    _register(client, email=email)
    wrong = client.post("/auth/login", json={"email": email, "password": "Wrong1234"})
    unknown = client.post("/auth/login", json={"email": _email(), "password": "Wrong1234"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_too_many_failures_lock_the_account_for_a_while(client):
    email = _email()
    _register(client, email=email)
    for _ in range(5):
        assert client.post("/auth/login", json={"email": email, "password": "Bad12345"}).status_code == 401
    locked = client.post("/auth/login", json={"email": email, "password": "Passw0rdOK"})
    assert locked.status_code == 429
    assert "Try again" in locked.json()["detail"]


def test_successful_login_resets_the_failure_counter(client):
    email = _email()
    _register(client, email=email)
    for _ in range(4):
        client.post("/auth/login", json={"email": email, "password": "Bad12345"})
    assert client.post("/auth/login", json={"email": email, "password": "Passw0rdOK"}).status_code == 200
    for _ in range(4):
        assert client.post("/auth/login", json={"email": email, "password": "Bad12345"}).status_code == 401


# ---------------- /auth/me ----------------

def test_me_needs_a_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_me_returns_the_logged_in_user(client):
    email = _email()
    token = _register(client, email=email).json()["token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert r.json()["age"] is None
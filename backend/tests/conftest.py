import os
import sys
import tempfile

# Use a throw-away SQLite database for tests (set BEFORE importing the app)
_db_file = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ.pop("ADMIN_API_KEY", None)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import auth_service

# Password hashing is deliberately slow, which makes the many register/login
# calls in the tests slow too. Tests use a cheaper setting (the real value in
# auth_service.py is untouched). Stored hashes remember their own settings,
# so this cannot affect real logins.
auth_service._N = 2 ** 10


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
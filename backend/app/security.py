import os
import secrets

from fastapi import Header, HTTPException


def require_admin(x_api_key: str | None = Header(default=None)):
    """
    Protects write endpoints (POST).

    If ADMIN_API_KEY is not set in the environment, the API stays open
    (convenient for local development). In production, set ADMIN_API_KEY
    and send it in the "X-API-Key" header.
    """

    expected = os.getenv("ADMIN_API_KEY")

    if not expected:
        return

    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

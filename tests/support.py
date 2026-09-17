"""Shared black-box HTTP helpers and constants for the test suite.

These only know the wire contract (contracts/openapi.yaml, specs/) — no
knowledge of src/url_shortener/*.py internals beyond the create_app()
factory used in conftest.py.
"""
from __future__ import annotations

import re
from datetime import datetime

BASE_URL = "https://short.example"
CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{7}$")
NOT_FOUND_DETAIL = "Short URL not found"
EXPIRED_DETAIL = "Short URL has expired"


def create(client, original_url="https://example.com", **extra):
    """POST /api/v1/urls with the given original_url and any extra fields (e.g. expires_at)."""
    payload = {"original_url": original_url, **extra}
    return client.post("/api/v1/urls", json=payload)


def create_active(client, original_url="https://example.com/target"):
    """Create a short URL and assert it succeeded; return the parsed ShortUrl body."""
    resp = create(client, original_url)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_with_expiry(client, expires_at_dt, original_url="https://example.com/expiring"):
    resp = create(client, original_url, expires_at=expires_at_dt.isoformat())
    assert resp.status_code == 201, resp.text
    return resp.json()


def redirect(client, code):
    return client.get(f"/{code}")


def metadata(client, code):
    return client.get(f"/api/v1/urls/{code}")


def click_count(client, code):
    return metadata(client, code).json()["click_count"]


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

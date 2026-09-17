"""Executable form of features/metadata.feature."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from freezegun import freeze_time

from tests.support import (
    NOT_FOUND_DETAIL,
    click_count,
    create_active,
    create_with_expiry,
    metadata,
    parse_ts,
    redirect,
)

REQUIRED_SHORT_URL_FIELDS = {"code", "original_url", "short_url", "click_count", "created_at"}


def test_metadata_for_an_active_short_url(client):
    record = create_active(client)
    code = record["code"]
    for _ in range(3):
        redirect(client, code)

    resp = metadata(client, code)

    assert resp.status_code == 200
    body = resp.json()
    assert REQUIRED_SHORT_URL_FIELDS <= body.keys()
    assert body["click_count"] == 3
    # The read itself must not have changed anything.
    assert click_count(client, code) == 3


def test_metadata_for_an_expired_short_url_is_still_retrievable(client):
    t0 = datetime.now(timezone.utc) - timedelta(days=2)
    expires_at = t0 + timedelta(hours=1)
    with freeze_time(t0):
        record = create_with_expiry(client, expires_at)

    resp = metadata(client, record["code"])

    assert resp.status_code == 200
    assert parse_ts(resp.json()["expires_at"]) < datetime.now(timezone.utc)


def test_metadata_for_unknown_code_returns_404(client):
    resp = metadata(client, "zzzzzzz")

    assert resp.status_code == 404
    assert resp.json()["detail"] == NOT_FOUND_DETAIL


def test_metadata_lookups_never_increment_click_count(client):
    record = create_active(client)
    code = record["code"]
    assert record["click_count"] == 0

    for _ in range(5):
        resp = metadata(client, code)
        assert resp.json()["click_count"] == 0

    assert click_count(client, code) == 0


def test_malformed_code_returns_404_not_422(client):
    resp = client.get("/api/v1/urls/ab")

    assert resp.status_code == 404

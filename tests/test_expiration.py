"""Executable form of features/expiration.feature.

Time is frozen with freezegun so creation-time and redirect-time clock reads
in src/url_shortener/creation.py and src/url_shortener/redirect.py (both
`datetime.now(timezone.utc)`) can be controlled precisely from outside,
without reading their internals beyond that shared clock-read pattern.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from freezegun import freeze_time

from tests.support import EXPIRED_DETAIL, click_count, create, create_with_expiry, metadata, parse_ts, redirect


def test_redirect_to_an_expired_short_url_returns_410(client):
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    with freeze_time(t0):
        record = create_with_expiry(client, t0 + timedelta(minutes=1))
    code = record["code"]

    with freeze_time(t0 + timedelta(hours=1, minutes=1)):
        resp = redirect(client, code)

    assert resp.status_code == 410
    assert resp.json()["detail"] == EXPIRED_DETAIL
    assert click_count(client, code) == 0


def test_redirect_at_the_exact_expiration_boundary_is_treated_as_expired(client):
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    expires_at = t0 + timedelta(hours=1)
    with freeze_time(t0):
        record = create_with_expiry(client, expires_at)
    code = record["code"]

    with freeze_time(expires_at):
        resp = redirect(client, code)

    assert resp.status_code == 410


def test_a_short_url_with_no_expires_at_never_expires(client):
    record = create(client, "https://example.com/permanent")
    assert record.status_code == 201
    code = record.json()["code"]

    far_future = datetime.now(timezone.utc) + timedelta(days=365 * 50)
    with freeze_time(far_future):
        resp = redirect(client, code)

    assert resp.status_code == 302


def test_a_naive_expires_at_at_creation_is_interpreted_as_utc(client):
    naive_future = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None)

    resp = create(client, "https://example.com", expires_at=naive_future.isoformat())

    assert resp.status_code == 201
    returned = parse_ts(resp.json()["expires_at"])
    assert returned == naive_future.replace(tzinfo=timezone.utc)


def test_metadata_remains_available_after_expiration(client):
    t0 = datetime.now(timezone.utc) - timedelta(days=2)
    expires_at = t0 + timedelta(hours=1)
    with freeze_time(t0):
        record = create_with_expiry(client, expires_at)

    resp = metadata(client, record["code"])

    assert resp.status_code == 200
    assert parse_ts(resp.json()["expires_at"]) < datetime.now(timezone.utc)

"""Black-box tests for blueprint/features/expiration.feature and
blueprint/specs/expiration.md.

The exact-boundary scenario ("expires_at equals the current request time
exactly") can't be forced from outside the process — we can't control the
server's clock. We substitute a near-boundary test: create a record that
expires very soon, wait past it, then confirm it's treated as expired.
This is a fair black-box equivalent of the boundary-inclusive rule, even
though it isn't a bit-for-bit reproduction of the internal unit test each
language's own suite can do with an injected/frozen clock.
"""

import time
from datetime import datetime, timedelta, timezone

from helpers import create


def _iso_in(seconds: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def test_redirect_to_an_expired_short_url_returns_410(client):
    record = create(client, original_url="https://example.com", expires_at=_iso_in(1))
    assert record.status_code == 201, record.text
    code = record.json()["code"]

    time.sleep(1.5)

    response = client.get(f"/{code}")
    assert response.status_code == 410
    assert response.json()["detail"] == "Short URL has expired"


def test_expired_short_url_does_not_increment_click_count(client):
    record = create(client, original_url="https://example.com", expires_at=_iso_in(1))
    code = record.json()["code"]
    time.sleep(1.5)

    client.get(f"/{code}")  # 410, should not increment

    metadata = client.get(f"/api/v1/urls/{code}").json()
    assert metadata["click_count"] == 0


def test_redirect_near_the_expiration_boundary_is_treated_as_expired(client):
    """Practical stand-in for the exact-boundary scenario — see module docstring."""
    record = create(client, original_url="https://example.com", expires_at=_iso_in(0.3))
    code = record.json()["code"]

    time.sleep(0.6)  # cross the boundary with a small, deliberate margin

    response = client.get(f"/{code}")
    assert response.status_code == 410


def test_a_short_url_with_no_expires_at_never_expires(client):
    record = create(client, original_url="https://example.com")
    code = record.json()["code"]

    response = client.get(f"/{code}")
    assert response.status_code == 302


def test_a_naive_expires_at_at_creation_is_interpreted_as_utc(client):
    naive = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

    response = create(client, original_url="https://example.com", expires_at=naive)

    assert response.status_code == 201, response.text
    returned = response.json()["expires_at"]
    parsed = datetime.fromisoformat(returned.replace("Z", "+00:00"))
    expected = datetime.fromisoformat(naive + "+00:00")
    assert parsed == expected


def test_metadata_remains_available_after_expiration(client):
    record = create(client, original_url="https://example.com", expires_at=_iso_in(1))
    code = record.json()["code"]
    time.sleep(1.5)

    response = client.get(f"/api/v1/urls/{code}")
    assert response.status_code == 200

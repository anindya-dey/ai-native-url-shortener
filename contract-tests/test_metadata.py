"""Black-box tests for blueprint/features/metadata.feature and
blueprint/specs/metadata.md, run against GET /api/v1/urls/{code} over HTTP."""

from helpers import create, create_active


def test_metadata_for_an_active_short_url(client):
    record = create_active(client)
    code = record["code"]
    client.get(f"/{code}")  # one redirect first, so click_count is nonzero
    client.get(f"/{code}")

    response = client.get(f"/api/v1/urls/{code}")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == code
    assert body["click_count"] == 2  # unchanged by this metadata GET


def test_metadata_for_an_expired_short_url_is_still_retrievable(client):
    created = create(
        client,
        original_url="https://example.com",
        expires_at="2000-01-01T00:00:00Z",
    )
    # Past expires_at is rejected at *creation* time (see
    # test_url_creation.py::test_past_expiration_is_rejected) — there's no
    # black-box way to create an already-expired record directly. We
    # substitute a short-lived one and wait for it to expire, which is a
    # fair black-box equivalent: create with a near-future expires_at, then
    # observe it via metadata after it has passed.
    assert created.status_code == 422  # sanity: confirms creation-time rejection

    import time

    from datetime import datetime, timedelta, timezone

    soon = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    record = create(client, original_url="https://example.com", expires_at=soon)
    assert record.status_code == 201, record.text
    code = record.json()["code"]

    time.sleep(1.5)

    response = client.get(f"/api/v1/urls/{code}")
    assert response.status_code == 200
    assert response.json()["expires_at"] is not None


def test_metadata_for_unknown_code_returns_404(client):
    response = client.get("/api/v1/urls/zzzzzzz")
    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_metadata_lookups_never_increment_click_count(client):
    record = create_active(client)
    code = record["code"]

    for _ in range(5):
        response = client.get(f"/api/v1/urls/{code}")
        assert response.status_code == 200

    assert client.get(f"/api/v1/urls/{code}").json()["click_count"] == 0


def test_malformed_code_returns_404_not_422(client):
    response = client.get("/api/v1/urls/ab")
    assert response.status_code == 404

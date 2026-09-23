"""Black-box tests for blueprint/features/url-creation.feature and
blueprint/specs/url-creation.md, run against POST /api/v1/urls over HTTP.

One scenario from the feature file is intentionally NOT reproduced here:
"Code collision is retried, not overwritten" requires stubbing the code
generator to force a collision, which is an internal implementation detail
each language's own test suite injects directly (see e.g.
rust/tests/url_creation.rs::code_collision_is_retried_not_overwritten). A
black-box HTTP client has no way to force that from outside. This is a
known, deliberate gap in this suite, not evidence the guarantee doesn't
hold — see README.md.
"""

import re
from datetime import datetime

from helpers import CODE_PATTERN, build_url_of_code_point_length, create


def _parse(iso_z: str) -> datetime:
    return datetime.fromisoformat(iso_z.replace("Z", "+00:00"))


def test_valid_destination_creates_a_short_url(client):
    response = create(client, original_url="https://example.com/a/long/path")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["original_url"] == "https://example.com/a/long/path"
    assert CODE_PATTERN.match(body["code"])
    assert body["click_count"] == 0
    assert body.get("expires_at") is None


def test_valid_destination_with_a_future_expiration(client):
    response = create(
        client,
        original_url="https://example.com",
        expires_at="2999-01-01T00:00:00Z",
    )
    assert response.status_code == 201, response.text
    # blueprint/GUARANTEES.md's round-trip guarantee is about representing
    # the same *instant*, not an identical string — e.g. trailing ".000"
    # milliseconds are a legitimate ISO 8601 rendering of the same instant.
    assert _parse(response.json()["expires_at"]) == _parse("2999-01-01T00:00:00Z")


def test_unsupported_scheme_is_rejected(client):
    response = create(client, original_url="ftp://example.com/file")
    assert response.status_code == 422


def test_malformed_url_is_rejected(client):
    response = create(client, original_url="not a url")
    assert response.status_code == 422


def test_oversized_original_url_is_rejected(client):
    response = create(client, original_url=build_url_of_code_point_length(2049))
    assert response.status_code == 422


def test_length_limit_counts_unicode_code_points_not_utf16_code_units(client):
    at_limit = build_url_of_code_point_length(2048)
    over_limit = build_url_of_code_point_length(2049)

    ok = create(client, original_url=at_limit)
    assert ok.status_code == 201, ok.text

    rejected = create(client, original_url=over_limit)
    assert rejected.status_code == 422, rejected.text


def test_scheme_only_url_with_no_host_is_rejected(client):
    response = create(client, original_url="https://")
    assert response.status_code == 422


def test_url_with_userinfo_but_no_host_is_rejected(client):
    response = create(client, original_url="https://user@/path")
    assert response.status_code == 422


def test_original_url_containing_control_characters_is_rejected(client):
    response = create(client, original_url="https://example.com/a\r\nb")
    assert response.status_code == 422


def test_missing_original_url_is_rejected(client):
    response = client.post("/api/v1/urls", json={})
    assert response.status_code == 422


def test_past_expiration_is_rejected(client):
    response = create(
        client,
        original_url="https://example.com",
        expires_at="2000-01-01T00:00:00Z",
    )
    assert response.status_code == 422


def test_short_url_is_built_from_the_configured_base_url_and_the_code(client, base_url):
    response = create(client, original_url="https://example.com")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["short_url"] == f"{base_url}/{body['code']}"
    assert re.match(rf"^{re.escape(base_url)}/[A-Za-z0-9]{{7}}$", body["short_url"])


def test_submitting_the_same_original_url_twice_creates_two_independent_codes(client):
    first = create(client, original_url="https://example.com/same")
    second = create(client, original_url="https://example.com/same")
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["code"] != second.json()["code"]


def test_unexpected_additional_field_is_rejected(client):
    """openapi.yaml's CreateUrlRequest declares additionalProperties: false."""
    response = client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com", "unexpected_field": "x"},
    )
    assert response.status_code == 422

"""Executable form of features/url-creation.feature.

Plain pytest, not pytest-bdd — see final report for the rationale. Test
names/docstrings map 1:1 to each scenario title; every Given/When/Then
assertion in the .feature file is exercised.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import url_shortener.creation as creation_module
from tests.support import BASE_URL, CODE_PATTERN, create, metadata, parse_ts


def test_valid_destination_creates_a_short_url(client):
    resp = create(client, "https://example.com/a/long/path")

    assert resp.status_code == 201
    body = resp.json()
    assert body["original_url"] == "https://example.com/a/long/path"
    assert CODE_PATTERN.fullmatch(body["code"])
    assert body["click_count"] == 0
    assert body["expires_at"] is None


def test_valid_destination_with_a_future_expiration(client):
    future = datetime.now(timezone.utc) + timedelta(hours=1)

    resp = create(client, "https://example.com", expires_at=future.isoformat())

    assert resp.status_code == 201
    assert parse_ts(resp.json()["expires_at"]) == future


def test_unsupported_scheme_is_rejected(client):
    resp = create(client, "ftp://example.com/file")
    assert resp.status_code == 422


def test_malformed_url_is_rejected(client):
    resp = create(client, "not a url")
    assert resp.status_code == 422


def test_oversized_original_url_is_rejected(client):
    prefix = "https://example.com/"
    long_url = prefix + "a" * (2049 - len(prefix))
    assert len(long_url) == 2049

    resp = create(client, long_url)

    assert resp.status_code == 422


def test_scheme_only_url_with_no_host_is_rejected(client):
    resp = create(client, "https://")
    assert resp.status_code == 422


def test_userinfo_only_url_with_no_host_is_rejected(client):
    """Regression coverage for the security-audit fix in
    src/url_shortener/models.py: host-emptiness is checked via
    urlparse(...).hostname, not .netloc. A userinfo component (user:pass@)
    makes .netloc non-empty even with no actual host, which previously let
    these slip past validation."""
    for bad_url in (
        "https://user:pass@",
        "https://@",
        "https://:80",
    ):
        resp = create(client, bad_url)
        assert resp.status_code == 422, bad_url


def test_userinfo_with_a_real_host_is_still_accepted(client):
    """Companion to the above: a URL with both userinfo AND a real host
    must not be rejected by the .hostname-based check."""
    resp = create(client, "https://user:pass@example.com")
    assert resp.status_code == 201


def test_original_url_containing_control_characters_is_rejected(client):
    for bad_url in (
        "https://example.com/\r",
        "https://example.com/\n",
        "https://example.com/\r\n/path",
    ):
        resp = create(client, bad_url)
        assert resp.status_code == 422, bad_url


def test_missing_original_url_is_rejected(client):
    resp = client.post("/api/v1/urls", json={})
    assert resp.status_code == 422


def test_past_expiration_is_rejected(client):
    past = datetime.now(timezone.utc) - timedelta(hours=1)

    resp = create(client, "https://example.com", expires_at=past.isoformat())

    assert resp.status_code == 422


def test_code_collision_is_retried_not_overwritten(client):
    """Force a real collision by stubbing url_shortener.creation.generate_code,
    the documented import seam in src/url_shortener/creation.py — not by
    reading business logic to decide what "correct" retry behavior looks
    like."""
    real_generate_code = creation_module.generate_code

    with patch("url_shortener.creation.generate_code", return_value="abc1234"):
        seed_resp = create(client, "https://existing.example.com")
    assert seed_resp.status_code == 201
    assert seed_resp.json()["code"] == "abc1234"

    calls = {"n": 0}

    def stub_generate_code():
        calls["n"] += 1
        return "abc1234" if calls["n"] == 1 else real_generate_code()

    with patch("url_shortener.creation.generate_code", side_effect=stub_generate_code):
        resp = create(client, "https://new.example.com")

    assert resp.status_code == 201
    assert resp.json()["code"] != "abc1234"

    existing = metadata(client, "abc1234")
    assert existing.status_code == 200
    assert existing.json()["original_url"] == "https://existing.example.com"


def test_collision_exhaustion_returns_503(client):
    """Regression coverage for the code-review addition in
    src/url_shortener/errors.py / src/url_shortener/creation.py
    (CodeGenerationExhaustedError): when every retry attempt keeps
    returning an already-taken code, creation fails closed with 503, not an
    unhandled 500. Not a features/url-creation.feature scenario — this is
    supporting behavior added by code review, tested directly here.
    """
    seed_resp = create(client, "https://existing.example.com")
    assert seed_resp.status_code == 201
    taken_code = seed_resp.json()["code"]

    with patch("url_shortener.creation.generate_code", return_value=taken_code):
        resp = create(client, "https://new.example.com")

    assert resp.status_code == 503
    assert resp.json() == {
        "detail": "Unable to generate a unique short URL code, please retry"
    }


def test_short_url_is_built_from_the_configured_base_url_and_the_code(client):
    resp = create(client, "https://example.com")

    assert resp.status_code == 201
    body = resp.json()
    assert body["short_url"] == f"{BASE_URL}/{body['code']}"


def test_submitting_the_same_original_url_twice_creates_two_independent_codes(client):
    first = create(client, "https://example.com/same")
    second = create(client, "https://example.com/same")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["code"] != second.json()["code"]


def test_oversized_request_body_is_rejected_before_reaching_the_route(client):
    """Regression coverage for the security-audit fix in
    src/url_shortener/main.py (MaxBodySizeMiddleware): a request whose
    Content-Length exceeds the 16384-byte cap is rejected with 413 at the
    ASGI middleware layer, before the route handler (and store) ever see
    it. Not a features/url-creation.feature scenario — this is supporting
    behavior added by security-audit review, tested directly here, same
    pattern as test_collision_exhaustion_returns_503 above.

    The declared Content-Length is overridden directly rather than sent
    with an actually-oversized body: httpx/TestClient forwards an explicit
    content-length header to the ASGI transport as-is without
    recalculating it from the real body, and the middleware only ever
    inspects the declared header — so this exercises the exact same code
    path a real oversized request would hit, without needing a 16KB+
    literal in the test.
    """
    resp = client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com"},
        headers={"content-length": "16385"},
    )

    assert resp.status_code == 413
    assert resp.json() == {"detail": "Request body too large"}


def test_request_body_at_or_under_the_cap_is_not_rejected_by_the_middleware(client):
    """Companion regression guard: the middleware must not false-positive
    on legitimate, normal-sized traffic. A body of exactly MAX_BODY_BYTES
    still reaches the route handler and succeeds (201) — the "normal
    request still works" case is already covered broadly by every other
    201 test in this file using the real, unmodified Content-Length that
    httpx computes; this test additionally pins the exact boundary."""
    resp = client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com"},
        headers={"content-length": "16384"},
    )

    assert resp.status_code == 201

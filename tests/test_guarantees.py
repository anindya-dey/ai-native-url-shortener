"""Property-based tests for GUARANTEES.md, using Hypothesis.

Each test's docstring names the exact GUARANTEES.md bullet it covers.

Pattern note: hypothesis's function-scoped-fixture health check fires when a
pytest fixture is passed as a `@given`-decorated function's own argument
(because that fixture would normally be re-created per test, which is wrong
mid-hypothesis-run). We avoid that by defining an inner function decorated
with `@given`/`@settings` *inside* the outer pytest test function, and
capturing the fixture (and any accumulator state that must persist across
examples, e.g. a "codes seen so far" set) via closure instead of as a
parameter. The outer test function still receives fixtures normally.
"""
from __future__ import annotations

import string
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.parse import quote

import url_shortener.creation as creation_module
from url_shortener.config import Settings
from url_shortener.main import create_app
from fastapi.testclient import TestClient
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from tests.strategies import (
    ascii_url_suffix,
    http_scheme,
    malformed_code,
    non_http_scheme,
    random_code,
    unicode_url_suffix,
)
from tests.support import (
    BASE_URL,
    CODE_PATTERN,
    NOT_FOUND_DETAIL,
    create,
    metadata,
    parse_ts,
    redirect,
)

PROP = settings(deadline=None, max_examples=200)
PROP_SMALL = settings(deadline=None, max_examples=30)


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------


def test_generated_codes_are_shaped_and_unique(client):
    """GUARANTEES: Code generation -> Shape; Uniqueness while active.
    Also covers short_url construction -> no two records share a short_url
    while active (a direct consequence, checked here too for free)."""
    seen_codes: set[str] = set()
    seen_short_urls: set[str] = set()

    @given(suffix=ascii_url_suffix)
    @PROP
    def run(suffix):
        resp = create(client, f"https://example.com/{suffix}")
        assert resp.status_code == 201
        body = resp.json()

        assert CODE_PATTERN.fullmatch(body["code"])
        assert body["code"] not in seen_codes
        assert body["short_url"] not in seen_short_urls
        seen_codes.add(body["code"])
        seen_short_urls.add(body["short_url"])

    run()


def test_collision_never_overwrites_existing_record():
    """GUARANTEES: Code generation -> No overwrite on collision.

    Each example gets its own fresh app/store (rather than sharing the
    `client` fixture across examples) because the seeded collision code is
    hypothesis-generated and could otherwise repeat across examples within
    one run, corrupting a later example's setup.
    """
    real_generate_code = creation_module.generate_code

    @given(
        existing_suffix=ascii_url_suffix,
        new_suffix=ascii_url_suffix,
        seed_code=random_code,
    )
    @PROP_SMALL
    def run(existing_suffix, new_suffix, seed_code):
        client = TestClient(create_app(base_url_override=BASE_URL), follow_redirects=False)
        existing_url = f"https://existing.example.com/{existing_suffix}"
        new_url = f"https://new.example.com/{new_suffix}"

        with patch("url_shortener.creation.generate_code", return_value=seed_code):
            seed_resp = create(client, existing_url)
        assert seed_resp.status_code == 201
        assert seed_resp.json()["code"] == seed_code

        calls = {"n": 0}

        def stub_generate_code():
            calls["n"] += 1
            return seed_code if calls["n"] == 1 else real_generate_code()

        with patch("url_shortener.creation.generate_code", side_effect=stub_generate_code):
            resp = create(client, new_url)

        assert resp.status_code == 201
        assert resp.json()["code"] != seed_code

        existing_meta = metadata(client, seed_code)
        assert existing_meta.status_code == 200
        assert existing_meta.json()["original_url"] == existing_url
        assert existing_meta.json()["click_count"] == 0

    run()


# ---------------------------------------------------------------------------
# Click tracking
# ---------------------------------------------------------------------------


def test_click_count_increases_by_exactly_n_for_sequential_redirects(client):
    """GUARANTEES: Click tracking -> Monotonic non-negative;
    Exactly-once per successful redirect."""

    @given(n=st.integers(min_value=1, max_value=20))
    @PROP_SMALL
    def run(n):
        record = create(client, "https://example.com/clicks").json()
        code = record["code"]
        assert record["click_count"] == 0

        for _ in range(n):
            assert redirect(client, code).status_code == 302

        final = metadata(client, code).json()["click_count"]
        assert final == n
        assert final >= 0

    run()


def test_failed_redirects_never_increment_click_count(client):
    """GUARANTEES: Click tracking -> No increment on failure (404 case)."""
    safe_code = create(client, "https://example.com/safe").json()["code"]

    @given(bad=malformed_code)
    @PROP
    def run(bad):
        resp = client.get(f"/{quote(bad, safe='')}")
        assert resp.status_code == 404
        assert metadata(client, safe_code).json()["click_count"] == 0

    run()


def test_expired_redirect_never_increments_click_count():
    """GUARANTEES: Click tracking -> No increment on failure (410 case)."""
    client = TestClient(create_app(base_url_override=BASE_URL), follow_redirects=False)

    from freezegun import freeze_time

    t0 = datetime.now(timezone.utc) - timedelta(days=1)
    expires_at = t0 + timedelta(minutes=1)
    with freeze_time(t0):
        record = create(client, "https://example.com/expired", expires_at=expires_at.isoformat()).json()
    code = record["code"]

    for _ in range(3):
        assert redirect(client, code).status_code == 410

    assert metadata(client, code).json()["click_count"] == 0


def test_metadata_reads_never_increment_click_count(client):
    """GUARANTEES: Click tracking -> No increment on metadata read."""
    code = create(client, "https://example.com/meta").json()["code"]

    @given(n=st.integers(min_value=1, max_value=30))
    @PROP_SMALL
    def run(n):
        for _ in range(n):
            assert metadata(client, code).json()["click_count"] == 0

    run()


# ---------------------------------------------------------------------------
# short_url construction
# ---------------------------------------------------------------------------


def test_short_url_reflects_current_base_url_not_a_stored_value(client, app):
    """GUARANTEES: short_url construction -> deterministic from code and
    configuration; never a stored literal that could go stale."""
    record = create(client, "https://example.com/base-url-check").json()
    code = record["code"]
    assert record["short_url"] == f"{BASE_URL}/{code}"

    new_base = "https://renamed.example"
    app.state.settings = Settings(base_url=new_base)

    resp = metadata(client, code)
    assert resp.json()["short_url"] == f"{new_base}/{code}"


# ---------------------------------------------------------------------------
# Duplicate submissions
# ---------------------------------------------------------------------------


def test_no_implicit_deduplication(client):
    """GUARANTEES: Duplicate submissions -> No implicit deduplication."""

    @given(suffix=ascii_url_suffix, n=st.integers(min_value=2, max_value=5))
    @PROP_SMALL
    def run(suffix, n):
        url = f"https://example.com/dup/{suffix}"
        codes = {create(client, url).json()["code"] for _ in range(n)}
        assert len(codes) == n

    run()


# ---------------------------------------------------------------------------
# Round-trip integrity
# ---------------------------------------------------------------------------


def test_original_url_round_trips_exactly_via_metadata(client):
    """GUARANTEES: Round-trip integrity -> Original URL is preserved exactly
    (metadata read)."""

    @given(scheme=http_scheme, suffix=unicode_url_suffix)
    @PROP
    def run(scheme, suffix):
        url = f"{scheme}://example.com/{suffix}"
        assume(len(url) <= 2048)

        resp = create(client, url)
        assert resp.status_code == 201
        code = resp.json()["code"]
        assert resp.json()["original_url"] == url
        assert metadata(client, code).json()["original_url"] == url

    run()


def test_original_url_round_trips_exactly_via_redirect_location(client):
    """GUARANTEES: Round-trip integrity -> Original URL is preserved exactly
    (redirect Location header).

    SPEC AMBIGUITY (flagged, not silently resolved): GUARANTEES.md says the
    Location header "reproduces that exact string" for *any* original_url,
    but raw HTTP header values are restricted to latin-1/ASCII-safe bytes at
    the ASGI/WSGI layer. Neither specs/url-creation.md nor
    specs/shared-conventions.md say whether original_url may contain
    characters outside that range, or how such a value should be
    represented in a Location header (reject at creation? percent-encode?
    RFC 8187 encode?). This test is restricted to ASCII-safe original_url
    values so it tests the guarantee where it unambiguously applies; the gap
    should be resolved in specs/url-creation.md (and a corresponding
    features/url-creation.feature scenario added) before non-ASCII
    original_url + Location-header behavior can be tested or guaranteed.
    """

    @given(scheme=http_scheme, suffix=ascii_url_suffix)
    @PROP
    def run(scheme, suffix):
        url = f"{scheme}://example.com/{suffix}"
        resp = create(client, url)
        assert resp.status_code == 201
        code = resp.json()["code"]

        assert redirect(client, code).headers["location"] == url

    run()


def test_expires_at_round_trips_as_the_same_utc_instant(client):
    """GUARANTEES: Round-trip integrity -> Timestamps round-trip in UTC, for
    naive input and for input in an arbitrary (non-UTC) fixed-offset
    timezone (per shared-conventions.md: "All stored and returned
    timestamps are UTC, regardless of input timezone")."""

    tz_offset_minutes = st.one_of(st.none(), st.integers(min_value=-12 * 60, max_value=14 * 60))

    @given(
        offset_minutes=tz_offset_minutes,
        delta_seconds=st.integers(min_value=30, max_value=60 * 60 * 24 * 30),
    )
    @PROP_SMALL
    def run(offset_minutes, delta_seconds):
        future_utc = datetime.now(timezone.utc) + timedelta(seconds=delta_seconds)

        if offset_minutes is None:
            submitted = future_utc.replace(tzinfo=None)
            expected_instant = submitted.replace(tzinfo=timezone.utc)
        else:
            tz = timezone(timedelta(minutes=offset_minutes))
            submitted = future_utc.astimezone(tz)
            expected_instant = submitted

        resp = create(client, "https://example.com/ts", expires_at=submitted.isoformat())
        assert resp.status_code == 201

        returned = parse_ts(resp.json()["expires_at"])
        assert returned == expected_instant

    run()


# ---------------------------------------------------------------------------
# Expiration
# ---------------------------------------------------------------------------


def test_records_without_expires_at_remain_active_arbitrarily_far_in_the_future(client):
    """GUARANTEES: Expiration -> Absence of expires_at means permanence."""
    code = create(client, "https://example.com/permanent").json()["code"]

    from freezegun import freeze_time

    @given(days=st.integers(min_value=1, max_value=365 * 200))
    @PROP_SMALL
    def run(days):
        future = datetime.now(timezone.utc) + timedelta(days=days)
        with freeze_time(future):
            resp = redirect(client, code)
        assert resp.status_code == 302

    run()


def test_creation_time_only_expiration_validation():
    """GUARANTEES: Validation -> Creation-time-only expiration validation.
    A past expires_at is rejected (422) at creation; once a record exists,
    a since-passed expires_at makes it "expired" (410 on redirect), never
    re-validated as "invalid" (422/400)."""
    client = TestClient(create_app(base_url_override=BASE_URL), follow_redirects=False)

    past = datetime.now(timezone.utc) - timedelta(hours=1)
    rejected = create(client, "https://example.com/past", expires_at=past.isoformat())
    assert rejected.status_code == 422

    from freezegun import freeze_time

    t0 = datetime.now(timezone.utc) - timedelta(days=1)
    expires_at = t0 + timedelta(minutes=1)
    with freeze_time(t0):
        record = create(client, "https://example.com/soon-expired", expires_at=expires_at.isoformat()).json()

    resp = redirect(client, record["code"])
    assert resp.status_code == 410
    assert resp.status_code not in (422, 400)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_scheme_restriction_is_exhaustive(client):
    """GUARANTEES: Validation -> Scheme restriction is exhaustive."""

    @given(scheme=non_http_scheme, suffix=ascii_url_suffix)
    @PROP
    def run(scheme, suffix):
        resp = create(client, f"{scheme}://example.com/{suffix}")
        assert resp.status_code == 422

    run()


def test_length_restriction_is_exhaustive(client):
    """GUARANTEES: Validation -> Length restriction is exhaustive."""
    prefix = "https://example.com/"

    @given(overflow=st.integers(min_value=1, max_value=5000))
    @PROP_SMALL
    def run(overflow):
        length = 2048 + overflow
        url = prefix + "a" * (length - len(prefix))
        assert len(url) == length

        resp = create(client, url)
        assert resp.status_code == 422

    run()


def test_malformed_and_missing_codes_are_indistinguishable(client):
    """GUARANTEES: Validation -> Malformed and missing codes are
    indistinguishable to the caller, for both GET /{code} and
    GET /api/v1/urls/{code}."""

    @given(bad=malformed_code)
    @PROP
    def run(bad):
        encoded = quote(bad, safe="")

        redirect_resp = client.get(f"/{encoded}")
        metadata_resp = client.get(f"/api/v1/urls/{encoded}")

        assert redirect_resp.status_code == 404
        assert redirect_resp.json()["detail"] == NOT_FOUND_DETAIL
        assert metadata_resp.status_code == 404
        assert metadata_resp.json()["detail"] == NOT_FOUND_DETAIL

    run()

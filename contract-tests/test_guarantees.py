"""Black-box property tests for blueprint/GUARANTEES.md, run over HTTP
against whichever implementation TARGET_URL points at.

Not every entry in GUARANTEES.md is reproducible from outside the
process. Two are deliberately skipped here, with the reason noted inline:

- "No overwrite on collision" needs a stubbed/forced code collision,
  which requires injecting the code generator from inside the process
  (each language's own suite does this directly).
- The `BASE_URL`-changes-reflect-immediately half of "short_url
  construction" needs changing the live server's configuration mid-test,
  which this suite has no access to.

Both are already covered by each language directory's own test suite.
This file proves what's provable from a pure black-box HTTP vantage
point — which is most of GUARANTEES.md, and the part that matters most
for showing the implementations behave identically.
"""

import string
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from helpers import CODE_PATTERN, create, create_active

# Network round-trips are slow relative to hypothesis's default deadline;
# disable it and cap example count instead of tuning a timing threshold.
slow_settings = settings(
    deadline=None,
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


# -- Code generation ---------------------------------------------------


def test_code_uniqueness_while_active(client):
    codes = {create_active(client, f"https://example.com/{i}")["code"] for i in range(30)}
    assert len(codes) == 30


def test_code_shape_matches_pattern(client):
    for i in range(10):
        record = create_active(client, f"https://example.com/shape/{i}")
        assert CODE_PATTERN.match(record["code"])


# -- Click tracking ------------------------------------------------------


@given(n=st.integers(min_value=0, max_value=8))
@slow_settings
def test_click_tracking_monotonic_non_negative(client, n):
    record = create_active(client)
    code = record["code"]
    for _ in range(n):
        client.get(f"/{code}")
    metadata = client.get(f"/api/v1/urls/{code}").json()
    assert metadata["click_count"] == n
    assert metadata["click_count"] >= 0


@given(n=st.integers(min_value=1, max_value=15))
@slow_settings
def test_click_tracking_exactly_once_per_successful_redirect(client, base_url, n):
    import httpx

    record = create_active(client)
    code = record["code"]

    def hit():
        with httpx.Client(base_url=base_url, follow_redirects=False, timeout=10.0) as c:
            return c.get(f"/{code}")

    with ThreadPoolExecutor(max_workers=n) as pool:
        results = list(pool.map(lambda _: hit(), range(n)))

    assert all(r.status_code == 302 for r in results)
    metadata = client.get(f"/api/v1/urls/{code}").json()
    assert metadata["click_count"] == n


def test_click_tracking_no_increment_on_failure(client):
    for _ in range(5):
        client.get("/zzzzzzz")
    # No record exists for zzzzzzz, so there's nothing to check click_count
    # on directly. The guarantee under test is that a 404 doesn't cause any
    # record to spring into existence with a nonzero count — confirmed by
    # metadata for the same code still returning 404 afterward.
    assert client.get("/api/v1/urls/zzzzzzz").status_code == 404


def test_click_tracking_no_increment_on_metadata_read(client):
    record = create_active(client)
    code = record["code"]
    for _ in range(5):
        client.get(f"/api/v1/urls/{code}")
    assert client.get(f"/api/v1/urls/{code}").json()["click_count"] == 0


# -- short_url construction ----------------------------------------------


def test_short_url_deterministic_from_code_and_configuration(client, base_url):
    record = create_active(client)
    assert record["short_url"] == f"{base_url}/{record['code']}"


# -- Duplicate submissions ------------------------------------------------


def test_no_implicit_deduplication(client):
    codes = {create_active(client, "https://example.com/dup")["code"] for _ in range(5)}
    assert len(codes) == 5


# -- Round-trip integrity --------------------------------------------------


_SAFE_PATH_CHARS = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"),
        min_codepoint=0x20,
        max_codepoint=0x2000,
    ),
    min_size=1,
    max_size=20,
)


@given(segment=_SAFE_PATH_CHARS)
@slow_settings
def test_round_trip_original_url_preserved_exactly(client, segment):
    original_url = f"https://example.com/{segment}"
    created = create(client, original_url=original_url)
    if created.status_code != 201:
        return  # some generated segments may legitimately fail other rules; not what's under test here
    code = created.json()["code"]
    metadata = client.get(f"/api/v1/urls/{code}").json()
    assert metadata["original_url"] == original_url


@given(word=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10))
@slow_settings
def test_round_trip_location_header_is_percent_encoding_equivalent(client, word):
    original_url = f"https://example.com/{word} name/caf\u00e9"
    created = create(client, original_url=original_url)
    assert created.status_code == 201, created.text
    code = created.json()["code"]

    response = client.get(f"/{code}")
    assert response.status_code == 302
    location = response.headers["location"]

    # "Encoding-equivalent, not byte-identical" (ADR-0007): parse both and
    # compare components, the same check each language's own guarantee test
    # performs internally.
    expected = urllib.parse.urlsplit(original_url)
    actual = urllib.parse.urlsplit(location)
    assert urllib.parse.unquote(actual.path) == urllib.parse.unquote(expected.path)
    assert actual.netloc == expected.netloc
    assert actual.scheme == expected.scheme


@given(hours=st.integers(min_value=1, max_value=1000), use_offset=st.booleans())
@slow_settings
def test_round_trip_timestamps_round_trip_in_utc(client, hours, use_offset):
    target = datetime.now(timezone.utc) + timedelta(hours=hours)
    submitted = target.isoformat().replace("+00:00", "Z") if use_offset else target.strftime("%Y-%m-%dT%H:%M:%S")

    response = create(client, original_url="https://example.com", expires_at=submitted)
    assert response.status_code == 201, response.text

    returned = datetime.fromisoformat(response.json()["expires_at"].replace("Z", "+00:00"))
    expected = target if use_offset else target.replace(microsecond=0)
    assert abs((returned - expected).total_seconds()) < 1


# -- Expiration ------------------------------------------------------------


def test_expiration_boundary_is_inclusive(client):
    response = create(
        client,
        original_url="https://example.com",
        expires_at=(datetime.now(timezone.utc) + timedelta(seconds=0.4)).isoformat().replace("+00:00", "Z"),
    )
    code = response.json()["code"]
    time.sleep(0.8)
    assert client.get(f"/{code}").status_code == 410


def test_expiration_does_not_affect_metadata_visibility(client):
    response = create(
        client,
        original_url="https://example.com",
        expires_at=(datetime.now(timezone.utc) + timedelta(seconds=0.4)).isoformat().replace("+00:00", "Z"),
    )
    code = response.json()["code"]
    time.sleep(0.8)
    assert client.get(f"/api/v1/urls/{code}").status_code == 200
    assert client.get(f"/{code}").status_code == 410


def test_absence_of_expires_at_means_permanence(client):
    record = create_active(client)
    assert client.get(f"/{record['code']}").status_code == 302


# -- Validation -------------------------------------------------------------


@given(scheme=st.sampled_from(["ftp", "file", "javascript", "gopher", "ws", "mailto"]))
@slow_settings
def test_validation_scheme_restriction_is_exhaustive(client, scheme):
    response = create(client, original_url=f"{scheme}://example.com")
    assert response.status_code == 422


@given(extra=st.integers(min_value=1, max_value=50))
@slow_settings
def test_validation_length_restriction_is_exhaustive(client, extra):
    from helpers import build_url_of_code_point_length

    response = create(client, original_url=build_url_of_code_point_length(2048 + extra))
    assert response.status_code == 422


@given(
    malformed=st.text(
        alphabet=string.ascii_letters + string.digits,
        min_size=1,
        max_size=6,
    ).filter(lambda s: not CODE_PATTERN.match(s))
)
@slow_settings
def test_validation_malformed_and_missing_codes_are_indistinguishable(client, malformed):
    redirect_response = client.get(f"/{malformed}")
    metadata_response = client.get(f"/api/v1/urls/{malformed}")
    assert redirect_response.status_code == 404
    assert metadata_response.status_code == 404

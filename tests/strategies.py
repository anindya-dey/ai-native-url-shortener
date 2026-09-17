"""Shared Hypothesis strategies for the GUARANTEES.md property tests."""
from __future__ import annotations

import re
import string

from hypothesis import strategies as st

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{7}$")


def _not_code_shaped(s: str) -> bool:
    return not CODE_PATTERN.fullmatch(s)


# Safe as both a JSON string value and a raw HTTP header value (Location).
ascii_url_suffix = st.text(
    alphabet=string.ascii_letters + string.digits + "-._~/?=&%",
    max_size=200,
)

# Wider unicode fragment: safe for JSON round-trip, NOT guaranteed header-safe.
unicode_url_suffix = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), max_codepoint=0x2FFF),
    max_size=200,
)

http_scheme = st.sampled_from(["http", "https"])

random_code = st.text(alphabet=string.ascii_letters + string.digits, min_size=7, max_size=7)

non_http_scheme = st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10).filter(
    lambda s: s not in ("http", "https")
)

# min_size=1: an empty path segment isn't a "malformed code" being routed to
# the {code} handler at all — GET / and GET /api/v1/urls/ don't match the
# {code} route (no segment supplied), so they hit FastAPI's generic 404
# instead of the app's custom "Short URL not found" handler. That's a
# routing fact, not a malformed-code case this guarantee is about.
#
# "." and ".." are excluded too: RFC 3986 dot-segment normalization means
# HTTP clients (httpx included) collapse a lone "." or ".." path segment
# before the request is even sent (GET /. becomes GET /), so those two
# literal values never reach the {code} handler as a path segment either —
# same routing-layer artifact as the empty-string case, not a malformed-code
# case this guarantee is about.
#
# \r and \n ARE included (unlike the exclusions above): they are NOT
# stripped or normalized away in transit — sent through the property test's
# quote(bad, safe="") encoding, they arrive as %0D/%0A and are correctly
# decoded back to literal \r/\n at the path-parameter level (verified
# directly against a running app). Excluding them here would have hidden
# exactly the class of bug that was previously live: is_valid_shape() used
# re.match() instead of re.fullmatch(), so "abc1234\n" was incorrectly
# accepted as well-formed. Only "/" is excluded from the alphabet, since it
# would split the generated string into multiple path segments.
_malformed_alphabet = [c for c in string.printable if c != "/"]
malformed_code = st.text(alphabet=_malformed_alphabet, min_size=1, max_size=20).filter(
    lambda s: _not_code_shaped(s) and s not in (".", "..")
)

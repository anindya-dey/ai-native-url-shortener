"""Small helpers shared across the black-box test files. No implementation
knowledge here — only what's derivable from blueprint/contracts/openapi.yaml
and blueprint/specs/."""

from __future__ import annotations

import re

import httpx

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{7}$")


def create(client: httpx.Client, **body) -> httpx.Response:
    """POST /api/v1/urls with an arbitrary JSON body."""
    return client.post("/api/v1/urls", json=body)


def create_active(client: httpx.Client, original_url: str = "https://example.com/target") -> dict:
    """Create a short URL with no expires_at and return the parsed ShortUrl body."""
    response = create(client, original_url=original_url)
    assert response.status_code == 201, response.text
    return response.json()


def build_url_of_code_point_length(code_points: int, filler: str = "\U0001f600") -> str:
    """Build an original_url with exactly `code_points` Unicode code points,
    using a character (default: an emoji requiring a UTF-16 surrogate pair)
    that a UTF-16-code-unit-counting implementation would double-count.
    Python's `len()` on `str` already counts code points, which is what we
    want here — we're constructing the *input*, not measuring it the way an
    implementation under test might (correctly or incorrectly)."""
    prefix = "https://example.com/"
    filler_count = code_points - len(prefix)
    if filler_count < 0:
        raise ValueError(f"code_points={code_points} too short for prefix {prefix!r}")
    return prefix + (filler * filler_count)

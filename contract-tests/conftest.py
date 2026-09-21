"""Shared fixtures for the black-box contract/guarantee suite.

This suite knows nothing about any implementation's language, framework,
or source code — only `../blueprint/contracts/openapi.yaml`,
`../blueprint/features/*.feature`, and `../blueprint/GUARANTEES.md`. It
talks to whichever server is listening at TARGET_URL over plain HTTP.
"""

import os

import httpx
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.environ.get("TARGET_URL")
    if not url:
        raise RuntimeError(
            "TARGET_URL must be set to the running implementation's address "
            '(e.g. TARGET_URL="http://127.0.0.1:8000"). Start that '
            "implementation's server first, with its own BASE_URL config set "
            "to the *same* value as TARGET_URL — this suite asserts "
            "`short_url` values against that assumption. See README.md."
        )
    return url.rstrip("/")


@pytest.fixture
def client(base_url: str):
    with httpx.Client(base_url=base_url, follow_redirects=False, timeout=10.0) as c:
        yield c

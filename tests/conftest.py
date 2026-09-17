import os

import pytest
from fastapi.testclient import TestClient

from tests.support import BASE_URL

# src/url_shortener/main.py builds a module-level singleton `app =
# create_app()` at import time using BASE_URL from the environment. Tests
# never use that singleton (see the `app`/`client` fixtures below, built via
# create_app() directly with base_url_override), but the module import
# itself needs BASE_URL set or it raises before we ever get to override
# anything.
os.environ.setdefault("BASE_URL", BASE_URL)

from url_shortener.main import create_app  # noqa: E402


@pytest.fixture
def app():
    """A fresh FastAPI app with its own in-memory Store, isolated per test."""
    return create_app(base_url_override=BASE_URL)


@pytest.fixture
def client(app):
    # follow_redirects=False so 302 responses are observable directly, since
    # almost every scenario asserts on the redirect itself, not its target.
    return TestClient(app, follow_redirects=False)

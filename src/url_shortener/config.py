import os
from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import Request


@dataclass(frozen=True)
class Settings:
    base_url: str


def _validate_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"BASE_URL must be an absolute http/https URL, got: {base_url!r}")
    if base_url.endswith("/"):
        raise ValueError(f"BASE_URL must not have a trailing slash, got: {base_url!r}")
    return base_url


def load_settings(base_url_override: str | None = None) -> Settings:
    base_url = base_url_override if base_url_override is not None else os.environ.get("BASE_URL")
    if not base_url:
        raise RuntimeError("BASE_URL environment variable is required and has no default")
    return Settings(base_url=_validate_base_url(base_url))


def get_settings(request: Request) -> Settings:
    return request.app.state.settings

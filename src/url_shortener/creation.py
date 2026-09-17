from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from url_shortener.codes import generate_code
from url_shortener.config import Settings, get_settings
from url_shortener.errors import BusinessValidationError, CodeGenerationExhaustedError
from url_shortener.models import CreateUrlRequest, ShortUrl, ShortUrlRecord
from url_shortener.store import Store, get_store

router = APIRouter()

MAX_CODE_ATTEMPTS = 10


def _normalize_expires_at(expires_at: datetime | None, now: datetime) -> datetime | None:
    if expires_at is None:
        return None
    if expires_at.tzinfo is None:
        normalized = expires_at.replace(tzinfo=timezone.utc)
    else:
        normalized = expires_at.astimezone(timezone.utc)
    if normalized <= now:
        raise BusinessValidationError("expires_at must be strictly in the future")
    return normalized


@router.post("/api/v1/urls", response_model=ShortUrl, status_code=status.HTTP_201_CREATED)
def create_short_url(
    payload: CreateUrlRequest,
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
) -> ShortUrl:
    now = datetime.now(timezone.utc)
    expires_at = _normalize_expires_at(payload.expires_at, now)

    for _ in range(MAX_CODE_ATTEMPTS):
        record = ShortUrlRecord(
            code=generate_code(),
            original_url=payload.original_url,
            click_count=0,
            created_at=now,
            expires_at=expires_at,
        )
        if store.insert_if_absent(record):
            return ShortUrl.from_record(record, settings.base_url)

    raise CodeGenerationExhaustedError(
        "Failed to generate a unique short URL code after multiple attempts"
    )

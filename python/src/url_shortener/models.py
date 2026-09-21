from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class CreateUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_url: str = Field(..., pattern=r"^https?://", max_length=2048)
    expires_at: datetime | None = None

    @field_validator("original_url")
    @classmethod
    def _validate_original_url(cls, value: str) -> str:
        if any(ord(ch) < 0x20 or 0x7F <= ord(ch) <= 0x9F for ch in value):
            raise ValueError("original_url must not contain control characters")
        if not urlparse(value).hostname:
            raise ValueError("original_url must include a non-empty host")
        return value


@dataclass(frozen=True)
class ShortUrlRecord:
    code: str
    original_url: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None


class ShortUrl(BaseModel):
    code: str
    original_url: str
    short_url: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None = None

    @field_serializer("created_at", "expires_at")
    def _serialize_utc(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @classmethod
    def from_record(cls, record: ShortUrlRecord, base_url: str) -> "ShortUrl":
        return cls(
            code=record.code,
            original_url=record.original_url,
            short_url=f"{base_url}/{record.code}",
            click_count=record.click_count,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )

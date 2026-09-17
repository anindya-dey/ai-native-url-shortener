import threading
from dataclasses import replace
from datetime import datetime
from enum import Enum

from fastapi import Request

from url_shortener.models import ShortUrlRecord


class RedirectHit(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"


class Store:
    def __init__(self) -> None:
        self._records: dict[str, ShortUrlRecord] = {}
        self._lock = threading.Lock()

    def insert_if_absent(self, record: ShortUrlRecord) -> bool:
        with self._lock:
            if record.code in self._records:
                return False
            self._records[record.code] = record
            return True

    def get(self, code: str) -> ShortUrlRecord | None:
        with self._lock:
            return self._records.get(code)

    def record_redirect_hit(
        self, code: str, now: datetime
    ) -> tuple[RedirectHit, ShortUrlRecord | None]:
        with self._lock:
            record = self._records.get(code)
            if record is None:
                return RedirectHit.NOT_FOUND, None
            if record.expires_at is not None and now >= record.expires_at:
                return RedirectHit.EXPIRED, record
            updated = replace(record, click_count=record.click_count + 1)
            self._records[code] = updated
            return RedirectHit.ACTIVE, updated


def get_store(request: Request) -> Store:
    return request.app.state.store

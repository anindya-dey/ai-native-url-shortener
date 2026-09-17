from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse

from url_shortener.codes import is_valid_shape
from url_shortener.errors import ShortUrlExpiredError, ShortUrlNotFoundError
from url_shortener.store import RedirectHit, Store, get_store

router = APIRouter()


@router.get("/{code}")
def redirect(code: str, store: Store = Depends(get_store)) -> Response:
    if not is_valid_shape(code):
        raise ShortUrlNotFoundError()

    now = datetime.now(timezone.utc)
    hit, record = store.record_redirect_hit(code, now)

    if hit is RedirectHit.NOT_FOUND:
        raise ShortUrlNotFoundError()
    if hit is RedirectHit.EXPIRED:
        raise ShortUrlExpiredError()

    return RedirectResponse(url=record.original_url, status_code=302)

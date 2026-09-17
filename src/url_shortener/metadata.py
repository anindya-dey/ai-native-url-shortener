from fastapi import APIRouter, Depends

from url_shortener.codes import is_valid_shape
from url_shortener.config import Settings, get_settings
from url_shortener.errors import ShortUrlNotFoundError
from url_shortener.models import ShortUrl
from url_shortener.store import Store, get_store

router = APIRouter()


@router.get("/api/v1/urls/{code}", response_model=ShortUrl)
def get_metadata(
    code: str,
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
) -> ShortUrl:
    if not is_valid_shape(code):
        raise ShortUrlNotFoundError()

    record = store.get(code)
    if record is None:
        raise ShortUrlNotFoundError()

    return ShortUrl.from_record(record, settings.base_url)

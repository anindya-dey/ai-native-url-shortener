import json

from fastapi import FastAPI

from url_shortener.config import load_settings
from url_shortener.creation import router as creation_router
from url_shortener.errors import register_exception_handlers
from url_shortener.metadata import router as metadata_router
from url_shortener.redirect import router as redirect_router
from url_shortener.store import Store

MAX_BODY_BYTES = 16384


class MaxBodySizeMiddleware:
    """Rejects requests whose declared Content-Length exceeds MAX_BODY_BYTES
    before the body is read, so oversized payloads are never buffered."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            content_length = next(
                (v for k, v in scope["headers"] if k == b"content-length"), None
            )
            if content_length is not None and int(content_length) > MAX_BODY_BYTES:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [(b"content-type", b"application/json")],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": json.dumps({"detail": "Request body too large"}).encode(),
                    }
                )
                return
        await self.app(scope, receive, send)


def create_app(base_url_override: str | None = None) -> FastAPI:
    app = FastAPI(title="URL Shortener")

    app.state.settings = load_settings(base_url_override)
    app.state.store = Store()

    register_exception_handlers(app)

    app.include_router(creation_router)
    app.include_router(metadata_router)
    app.include_router(redirect_router)

    app.add_middleware(MaxBodySizeMiddleware)

    return app


app = create_app()

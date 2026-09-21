from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ShortUrlNotFoundError(Exception):
    pass


class ShortUrlExpiredError(Exception):
    pass


class BusinessValidationError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class CodeGenerationExhaustedError(Exception):
    pass


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ShortUrlNotFoundError)
    def _handle_not_found(request: Request, exc: ShortUrlNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Short URL not found"})

    @app.exception_handler(ShortUrlExpiredError)
    def _handle_expired(request: Request, exc: ShortUrlExpiredError) -> JSONResponse:
        return JSONResponse(status_code=410, content={"detail": "Short URL has expired"})

    @app.exception_handler(CodeGenerationExhaustedError)
    def _handle_code_generation_exhausted(
        request: Request, exc: CodeGenerationExhaustedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Unable to generate a unique short URL code, please retry"},
        )

    @app.exception_handler(BusinessValidationError)
    def _handle_business_validation(
        request: Request, exc: BusinessValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    def _handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        message = "; ".join(
            f"{'.'.join(str(loc) for loc in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        return JSONResponse(status_code=422, content={"detail": message})

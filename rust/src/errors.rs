//! Error response construction — `blueprint/specs/shared-conventions.md`
//! ("Errors") and the `ValidationError`/`NotFoundError`/`ExpiredError`
//! schemas in `blueprint/contracts/openapi.yaml`.

use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;

use crate::schemas::ErrorBody;

pub fn validation_error(detail: impl Into<String>) -> Response {
    (StatusCode::UNPROCESSABLE_ENTITY, Json(ErrorBody::new(detail))).into_response()
}

pub fn not_found() -> Response {
    (StatusCode::NOT_FOUND, Json(ErrorBody::new("Short URL not found"))).into_response()
}

pub fn gone_expired() -> Response {
    (StatusCode::GONE, Json(ErrorBody::new("Short URL has expired"))).into_response()
}

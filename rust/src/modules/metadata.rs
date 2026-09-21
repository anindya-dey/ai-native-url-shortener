//! Metadata module — `GET /api/v1/urls/{code}`.
//!
//! Owns: read-only lookup of a short URL record, expired or not — no
//! writes, and deliberately no expiration check
//! (`blueprint/MODULE_BOUNDARIES.md`, "Metadata"). Governed by
//! `blueprint/specs/metadata.md`.

use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;

use crate::app::AppState;
use crate::codes::is_valid_code_shape;
use crate::errors::not_found;
use crate::schemas::ShortUrl;

pub async fn get_metadata(State(state): State<AppState>, Path(code): Path<String>) -> Response {
    if !is_valid_code_shape(&code) {
        return not_found();
    }

    let Some(record) = state.store.get(&code) else {
        return not_found();
    };

    (StatusCode::OK, Json(ShortUrl {
        code: record.code.clone(),
        original_url: record.original_url,
        short_url: format!("{}/{}", state.base_url, record.code),
        click_count: record.click_count,
        created_at: record.created_at,
        expires_at: record.expires_at,
    }))
        .into_response()
}

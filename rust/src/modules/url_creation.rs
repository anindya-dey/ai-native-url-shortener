//! URL creation module — `POST /api/v1/urls`.
//!
//! Owns: generating and persisting new short URL records (including
//! collision retry) and validating/normalizing `expires_at` at creation
//! time. Governed by `blueprint/specs/url-creation.md` and the
//! creation-time slice of `blueprint/specs/expiration.md`. See
//! `blueprint/MODULE_BOUNDARIES.md` ("URL creation").

use axum::extract::State;
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::{body::Bytes, Json};
use chrono::Utc;

use crate::app::AppState;
use crate::codes::generate_code;
use crate::errors::validation_error;
use crate::expiration::is_strictly_future;
use crate::schemas::{CreateUrlRequest, ShortUrl};
use crate::timestamps::parse_expires_at;

/// `blueprint/specs/url-creation.md`: C0/C1 control characters, including
/// `\r` and `\n`, are rejected anywhere in `original_url`. Checked on the
/// raw string *before* parsing, because `url::Url::parse` silently strips
/// ASCII tab/CR/LF rather than rejecting them (the same WHATWG-parser
/// quirk noted for the TypeScript implementation's URL parser in
/// `blueprint/lineage/0002-typescript-system-initial-generation.md`).
fn contains_control_character(s: &str) -> bool {
    s.chars().any(|c| matches!(c as u32, 0x00..=0x1F | 0x7F | 0x80..=0x9F))
}

/// Validates `original_url` per `blueprint/specs/url-creation.md`.
/// "Characters" means Unicode code points (`char::count`), not UTF-16
/// code units — `str::chars` already iterates Unicode scalar values, so
/// this holds without any extra surrogate-pair handling (verified in
/// `tests/url_creation.rs`, unlike the UTF-16-based length check that
/// needed an explicit fix in the TypeScript implementation).
fn validate_original_url(original_url: &str) -> Result<(), &'static str> {
    if original_url.chars().count() > 2048 {
        return Err("original_url must be at most 2048 characters");
    }
    if contains_control_character(original_url) {
        return Err("original_url must not contain control characters");
    }
    let url = url::Url::parse(original_url).map_err(|_| "original_url must be a valid URL")?;
    if url.scheme() != "http" && url.scheme() != "https" {
        return Err("original_url must use the http or https scheme");
    }
    if url.host_str().is_none_or(|h| h.is_empty()) {
        return Err("original_url must include a non-empty host");
    }
    Ok(())
}

pub async fn create_short_url(State(state): State<AppState>, body: Bytes) -> Response {
    let request: CreateUrlRequest = match serde_json::from_slice(&body) {
        Ok(request) => request,
        Err(_) => return validation_error("Request body is not a valid CreateUrlRequest"),
    };

    let Some(original_url) = request.original_url else {
        return validation_error("original_url is required");
    };
    if let Err(detail) = validate_original_url(&original_url) {
        return validation_error(detail);
    }

    let expires_at = match request.expires_at {
        None => None,
        Some(raw) => {
            let Some(parsed) = parse_expires_at(&raw) else {
                return validation_error("expires_at must be a valid ISO 8601 timestamp");
            };
            if !is_strictly_future(parsed, Utc::now()) {
                return validation_error("expires_at must be strictly in the future");
            }
            Some(parsed)
        }
    };

    let record = state.store.create(original_url, expires_at, generate_code);

    (StatusCode::CREATED, Json(ShortUrl {
        code: record.code.clone(),
        original_url: record.original_url,
        short_url: format!("{}/{}", state.base_url, record.code),
        click_count: record.click_count,
        created_at: record.created_at,
        expires_at: record.expires_at,
    }))
        .into_response()
}

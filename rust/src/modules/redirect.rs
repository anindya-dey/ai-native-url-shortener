//! Redirect module — `GET /{code}`.
//!
//! Owns: looking up a code, checking expiration, issuing the redirect,
//! and incrementing `click_count` — the only place in the system that
//! writes `click_count` (`blueprint/MODULE_BOUNDARIES.md`, "Redirect").
//! Governed by `blueprint/specs/redirects.md` and the redirect-time slice
//! of `blueprint/specs/expiration.md`.

use axum::extract::{Path, State};
use axum::http::{header, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use chrono::Utc;
use percent_encoding::{utf8_percent_encode, AsciiSet, CONTROLS};

use crate::app::AppState;
use crate::codes::is_valid_code_shape;
use crate::errors::{gone_expired, not_found};
use crate::expiration::is_expired;

/// Characters that are unsafe to place literally in an HTTP header value.
/// Percent-encoding only these (and leaving everything else, including an
/// existing `%XX` escape, untouched) satisfies
/// `blueprint/decisions/ADR-0007-location-header-preserves-percent-encoding.md`:
/// the header dereferences to the identical resource without the extra,
/// unrelated normalization (trailing-slash addition, scheme
/// lower-casing, ...) that re-serializing through a full URL parser
/// would introduce.
const HEADER_UNSAFE: &AsciiSet = &CONTROLS
    .add(b' ')
    .add(b'"')
    .add(b'<')
    .add(b'>')
    .add(b'\\')
    .add(b'^')
    .add(b'`')
    .add(b'{')
    .add(b'|')
    .add(b'}');

fn location_header_value(original_url: &str) -> HeaderValue {
    let encoded = utf8_percent_encode(original_url, HEADER_UNSAFE).to_string();
    HeaderValue::from_str(&encoded).expect("percent-encoded URL is a valid header value")
}

pub async fn redirect(State(state): State<AppState>, Path(code): Path<String>) -> Response {
    if !is_valid_code_shape(&code) {
        return not_found();
    }

    let Some(record) = state.store.get(&code) else {
        return not_found();
    };

    if is_expired(record.expires_at, Utc::now()) {
        return gone_expired();
    }

    state.store.increment_click_count(&code);

    (
        StatusCode::FOUND,
        [(header::LOCATION, location_header_value(&record.original_url))],
    )
        .into_response()
}

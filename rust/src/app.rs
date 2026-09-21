//! Wires the three modules onto their routes from
//! `blueprint/contracts/openapi.yaml`. Shared by `main.rs` and the
//! integration tests in `tests/`.

use std::sync::Arc;

use axum::routing::{get, post};
use axum::Router;

use crate::modules::{metadata, redirect, url_creation};
use crate::store::Store;

#[derive(Clone)]
pub struct AppState {
    pub store: Arc<Store>,
    pub base_url: Arc<String>,
}

pub fn build_app(base_url: String, store: Arc<Store>) -> Router {
    let state = AppState { store, base_url: Arc::new(base_url) };

    Router::new()
        .route("/api/v1/urls", post(url_creation::create_short_url))
        .route("/api/v1/urls/:code", get(metadata::get_metadata))
        .route("/:code", get(redirect::redirect))
        .with_state(state)
}

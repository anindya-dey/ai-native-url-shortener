#![allow(dead_code)] // Every method is used by at least one test binary, but each binary only sees its own usage.

//! Shared test harness: builds the real axum `Router` (same code path as
//! `main.rs`) backed by a fresh in-memory `Store` per test, and drives it
//! with `tower::ServiceExt::oneshot` — no real socket needed. Cloning
//! `TestApp` clones the `Router`, which shares the same `Arc<Store>`, so
//! concurrent clones still hit one store — this is what makes the
//! concurrency property test in `guarantees.rs` a genuine proof rather
//! than a single-threaded stand-in.

use std::sync::Arc;

use axum::body::{Body, Bytes};
use axum::http::{HeaderMap, Request, StatusCode};
use axum::Router;
use chrono::{DateTime, Utc};
use http_body_util::BodyExt;
use serde_json::Value;
use tower::ServiceExt;

use url_shortener::app::build_app;
use url_shortener::store::Store;

pub const BASE_URL: &str = "https://short.example";

#[derive(Clone)]
pub struct TestApp {
    router: Router,
    pub store: Arc<Store>,
}

pub struct RawResponse {
    pub status: StatusCode,
    pub headers: HeaderMap,
    pub body: Bytes,
}

impl RawResponse {
    pub fn json(&self) -> Value {
        serde_json::from_slice(&self.body).expect("response body is valid JSON")
    }

    pub fn location(&self) -> &str {
        self.headers.get("location").unwrap().to_str().unwrap()
    }
}

impl TestApp {
    pub fn new() -> Self {
        Self::with_base_url(BASE_URL)
    }

    pub fn with_base_url(base_url: &str) -> Self {
        let store = Arc::new(Store::new());
        let router = build_app(base_url.to_string(), store.clone());
        Self { router, store }
    }

    /// Same store, a different `AppState`/`Router` built with a different
    /// `BASE_URL` — used to prove `short_url` is recomputed from current
    /// configuration, not stored (`GUARANTEES.md`, "short_url
    /// construction").
    pub fn with_same_store_and_base_url(&self, base_url: &str) -> Self {
        let router = build_app(base_url.to_string(), self.store.clone());
        Self { router, store: self.store.clone() }
    }

    /// Directly inserts a record, bypassing the HTTP layer, for Given
    /// steps like "an existing, unexpired short URL with code X".
    pub fn seed(&self, code: &str, original_url: &str, expires_at: Option<DateTime<Utc>>) {
        self.store
            .create(original_url.to_string(), expires_at, move || code.to_string());
    }

    pub fn click_count(&self, code: &str) -> Option<u64> {
        self.store.get(code).map(|r| r.click_count)
    }

    pub async fn post_urls(&self, body: Value) -> RawResponse {
        self.send(
            Request::builder()
                .method("POST")
                .uri("/api/v1/urls")
                .header("content-type", "application/json")
                .body(Body::from(body.to_string()))
                .unwrap(),
        )
        .await
    }

    pub async fn post_urls_raw_body(&self, body: &str) -> RawResponse {
        self.send(
            Request::builder()
                .method("POST")
                .uri("/api/v1/urls")
                .header("content-type", "application/json")
                .body(Body::from(body.to_string()))
                .unwrap(),
        )
        .await
    }

    pub async fn get_metadata(&self, code: &str) -> RawResponse {
        self.get(&format!("/api/v1/urls/{code}")).await
    }

    pub async fn get_redirect(&self, code: &str) -> RawResponse {
        self.get(&format!("/{code}")).await
    }

    pub async fn get(&self, path: &str) -> RawResponse {
        self.send(Request::builder().method("GET").uri(path).body(Body::empty()).unwrap())
            .await
    }

    async fn send(&self, request: Request<Body>) -> RawResponse {
        let response = self.router.clone().oneshot(request).await.unwrap();
        let status = response.status();
        let headers = response.headers().clone();
        let body = response.into_body().collect().await.unwrap().to_bytes();
        RawResponse { status, headers, body }
    }
}

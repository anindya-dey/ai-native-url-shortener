//! Executable scenarios for `blueprint/features/metadata.feature`.
//! Source of truth: `blueprint/specs/metadata.md`.

mod support;

use chrono::{Duration, Utc};
use support::TestApp;

#[tokio::test]
async fn metadata_for_an_active_short_url() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", None);
    for _ in 0..3 {
        app.get_redirect("abc1234").await;
    }

    let response = app.get_metadata("abc1234").await;

    assert_eq!(response.status, 200);
    let body = response.json();
    assert_eq!(body["code"], "abc1234");
    assert_eq!(body["click_count"], 3);
}

#[tokio::test]
async fn metadata_for_an_expired_short_url_is_still_retrievable() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", Some(Utc::now() - Duration::hours(1)));

    let response = app.get_metadata("abc1234").await;

    assert_eq!(response.status, 200);
    let expires_at: chrono::DateTime<Utc> = response.json()["expires_at"].as_str().unwrap().parse().unwrap();
    assert!(expires_at < Utc::now());
}

#[tokio::test]
async fn metadata_for_unknown_code_returns_404() {
    let app = TestApp::new();
    let response = app.get_metadata("zzzzzzz").await;
    assert_eq!(response.status, 404);
    assert_eq!(response.json()["detail"], "Short URL not found");
}

#[tokio::test]
async fn metadata_lookups_never_increment_click_count() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", None);

    for _ in 0..5 {
        app.get_metadata("abc1234").await;
    }

    assert_eq!(app.click_count("abc1234"), Some(0));
}

#[tokio::test]
async fn malformed_code_returns_404_not_422() {
    let app = TestApp::new();
    let response = app.get_metadata("ab").await;
    assert_eq!(response.status, 404);
}

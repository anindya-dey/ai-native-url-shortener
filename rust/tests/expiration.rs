//! Executable scenarios for `blueprint/features/expiration.feature`.
//! Source of truth: `blueprint/specs/expiration.md`.

mod support;

use chrono::{Duration, SubsecRound, Utc};
use serde_json::json;
use support::TestApp;

#[tokio::test]
async fn redirect_to_an_expired_short_url_returns_410() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", Some(Utc::now() - Duration::hours(1)));

    let response = app.get_redirect("abc1234").await;

    assert_eq!(response.status, 410);
    assert_eq!(response.json()["detail"], "Short URL has expired");
    assert_eq!(app.click_count("abc1234"), Some(0));
}

#[tokio::test]
async fn redirect_at_the_exact_expiration_boundary_is_treated_as_expired() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", Some(Utc::now()));

    let response = app.get_redirect("abc1234").await;

    assert_eq!(response.status, 410);
}

#[tokio::test]
async fn a_short_url_with_no_expires_at_never_expires() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", None);

    let response = app.get_redirect("abc1234").await;

    assert_eq!(response.status, 302);
}

#[tokio::test]
async fn a_naive_expires_at_at_creation_is_interpreted_as_utc() {
    let app = TestApp::new();
    let future = Utc::now() + Duration::hours(1);
    let naive = future.format("%Y-%m-%dT%H:%M:%S").to_string();

    let response = app
        .post_urls(json!({ "original_url": "https://example.com", "expires_at": naive }))
        .await;

    assert_eq!(response.status, 201);
    let returned: chrono::DateTime<Utc> = response.json()["expires_at"].as_str().unwrap().parse().unwrap();
    assert_eq!(returned, future.trunc_subsecs(0));
}

#[tokio::test]
async fn metadata_remains_available_after_expiration() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", Some(Utc::now() - Duration::hours(1)));

    let response = app.get_metadata("abc1234").await;

    assert_eq!(response.status, 200);
    let expires_at: chrono::DateTime<Utc> = response.json()["expires_at"].as_str().unwrap().parse().unwrap();
    assert!(expires_at < Utc::now());
}

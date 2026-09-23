//! Executable scenarios for `blueprint/features/url-creation.feature`,
//! one test per scenario title. Source of truth for the rules under test:
//! `blueprint/specs/url-creation.md`.

mod support;

use chrono::{Duration, Utc};
use serde_json::json;
use support::TestApp;

#[tokio::test]
async fn valid_destination_creates_a_short_url() {
    let app = TestApp::new();
    let response = app.post_urls(json!({ "original_url": "https://example.com/a/long/path" })).await;

    assert_eq!(response.status, 201);
    let body = response.json();
    assert_eq!(body["original_url"], "https://example.com/a/long/path");
    assert!(body["code"].as_str().unwrap().chars().count() == 7);
    assert_eq!(body["click_count"], 0);
    assert!(body["expires_at"].is_null());
}

#[tokio::test]
async fn valid_destination_with_a_future_expiration() {
    let app = TestApp::new();
    let expires_at = Utc::now() + Duration::hours(1);
    let response = app
        .post_urls(json!({ "original_url": "https://example.com", "expires_at": expires_at.to_rfc3339() }))
        .await;

    assert_eq!(response.status, 201);
    let body = response.json();
    let returned: chrono::DateTime<Utc> = body["expires_at"].as_str().unwrap().parse().unwrap();
    assert_eq!(returned, expires_at);
}

#[tokio::test]
async fn unsupported_scheme_is_rejected() {
    let app = TestApp::new();
    let response = app.post_urls(json!({ "original_url": "ftp://example.com/file" })).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn malformed_url_is_rejected() {
    let app = TestApp::new();
    let response = app.post_urls(json!({ "original_url": "not a url" })).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn oversized_original_url_is_rejected() {
    let app = TestApp::new();
    let too_long = "https://example.com/".to_string() + &"a".repeat(2049 - "https://example.com/".chars().count());
    assert_eq!(too_long.chars().count(), 2049);
    let response = app.post_urls(json!({ "original_url": too_long })).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn length_limit_counts_unicode_code_points_not_utf16_code_units() {
    let app = TestApp::new();
    let prefix = "https://example.com/";
    let surrogate_pair_char = '😀'; // requires a UTF-16 surrogate pair
    let padding = prefix.chars().count();
    let mut exactly_2048 = prefix.to_string();
    exactly_2048.extend(std::iter::repeat_n(surrogate_pair_char, 2048 - padding));
    assert_eq!(exactly_2048.chars().count(), 2048);

    let response = app.post_urls(json!({ "original_url": exactly_2048.clone() })).await;
    assert_eq!(response.status, 201);

    let mut exactly_2049 = exactly_2048;
    exactly_2049.push(surrogate_pair_char);
    assert_eq!(exactly_2049.chars().count(), 2049);

    let response = app.post_urls(json!({ "original_url": exactly_2049 })).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn scheme_only_url_with_no_host_is_rejected() {
    let app = TestApp::new();
    let response = app.post_urls(json!({ "original_url": "https://" })).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn url_with_userinfo_but_no_host_is_rejected() {
    let app = TestApp::new();
    let response = app.post_urls(json!({ "original_url": "https://user@/path" })).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn original_url_containing_control_characters_is_rejected() {
    let app = TestApp::new();
    let response = app.post_urls(json!({ "original_url": "https://example.com/a\r\nb" })).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn missing_original_url_is_rejected() {
    let app = TestApp::new();
    let response = app.post_urls(json!({})).await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn past_expiration_is_rejected() {
    let app = TestApp::new();
    let expires_at = Utc::now() - Duration::hours(1);
    let response = app
        .post_urls(json!({ "original_url": "https://example.com", "expires_at": expires_at.to_rfc3339() }))
        .await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn code_collision_is_retried_not_overwritten() {
    let app = TestApp::new();
    app.seed("abc1234", "https://existing.example.com", None);

    // Force the store's next code generation to collide first, then
    // succeed, by inserting directly through the store with a stubbed
    // generator that mirrors what the HTTP-level collision would do.
    let record = app.store.create("https://new.example.com".to_string(), None, {
        let mut attempts = vec!["abc1234".to_string(), "different".chars().take(7).collect()].into_iter();
        move || attempts.next().unwrap()
    });

    assert_ne!(record.code, "abc1234");
    let existing = app.store.get("abc1234").unwrap();
    assert_eq!(existing.original_url, "https://existing.example.com");
}

#[tokio::test]
async fn short_url_is_built_from_the_configured_base_url_and_the_code() {
    let app = TestApp::with_base_url("https://short.example");
    let response = app.post_urls(json!({ "original_url": "https://example.com" })).await;

    let body = response.json();
    let code = body["code"].as_str().unwrap();
    let short_url = body["short_url"].as_str().unwrap();
    assert!(short_url.starts_with("https://short.example/"));
    assert!(short_url.ends_with(code));
}

/// Not a named feature scenario, but a direct requirement of
/// `CreateUrlRequest`'s `additionalProperties: false` in
/// `blueprint/contracts/openapi.yaml`.
#[tokio::test]
async fn unexpected_additional_field_is_rejected() {
    let app = TestApp::new();
    let response = app
        .post_urls_raw_body(r#"{"original_url":"https://example.com","unexpected":"field"}"#)
        .await;
    assert_eq!(response.status, 422);
}

#[tokio::test]
async fn submitting_the_same_original_url_twice_creates_two_independent_codes() {
    let app = TestApp::new();
    let first = app.post_urls(json!({ "original_url": "https://example.com/same" })).await;
    let second = app.post_urls(json!({ "original_url": "https://example.com/same" })).await;

    assert_eq!(first.status, 201);
    assert_eq!(second.status, 201);
    assert_ne!(first.json()["code"], second.json()["code"]);
}

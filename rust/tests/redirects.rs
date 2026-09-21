//! Executable scenarios for `blueprint/features/redirects.feature`.
//! Source of truth: `blueprint/specs/redirects.md`.

mod support;

use support::TestApp;

#[tokio::test]
async fn redirect_to_an_active_short_url() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", None);

    let response = app.get_redirect("abc1234").await;

    assert_eq!(response.status, 302);
    assert_eq!(response.location(), "https://example.com/target");
    assert_eq!(app.click_count("abc1234"), Some(1));
}

#[tokio::test]
async fn unknown_code_returns_404() {
    let app = TestApp::new();
    let response = app.get_redirect("zzzzzzz").await;
    assert_eq!(response.status, 404);
    assert_eq!(response.json()["detail"], "Short URL not found");
}

#[tokio::test]
async fn repeated_redirects_accumulate_click_count() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", None);
    for _ in 0..5 {
        app.get_redirect("abc1234").await;
    }

    let response = app.get_redirect("abc1234").await;
    assert_eq!(response.status, 302);
    assert_eq!(app.click_count("abc1234"), Some(6));
}

#[tokio::test]
async fn concurrent_redirects_do_not_lose_click_count() {
    let app = TestApp::new();
    app.seed("abc1234", "https://example.com/target", None);

    let handles: Vec<_> = (0..10)
        .map(|_| {
            let app = app.clone();
            tokio::spawn(async move { app.get_redirect("abc1234").await })
        })
        .collect();
    for handle in handles {
        handle.await.unwrap();
    }

    assert_eq!(app.click_count("abc1234"), Some(10));
}

#[tokio::test]
async fn a_404_response_does_not_modify_click_count() {
    let app = TestApp::new();
    app.get_redirect("zzzzzzz").await;
    assert_eq!(app.click_count("zzzzzzz"), None);
}

#[tokio::test]
async fn malformed_code_returns_404_not_422() {
    let app = TestApp::new();
    let response = app.get_redirect("ab").await;
    assert_eq!(response.status, 404);
    assert_eq!(response.json()["detail"], "Short URL not found");
}

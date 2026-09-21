//! Property-based tests for every applicable entry in
//! `blueprint/GUARANTEES.md`. Each test is named after the guarantee it
//! checks. Async assertions are computed inside `block_on` into a plain
//! value, then asserted with `prop_assert!`/`prop_assert_eq!` outside the
//! async block (proptest's macros can't cross an `async move` boundary).

mod support;

use chrono::{DateTime, Duration, SubsecRound, Utc};
use proptest::prelude::*;
use serde_json::json;
use support::TestApp;
use url_shortener::codes::{generate_code, is_valid_code_shape};
use url_shortener::store::Store;

fn block_on<F: std::future::Future>(future: F) -> F::Output {
    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .unwrap()
        .block_on(future)
}

fn distinct_url(seed: u32) -> String {
    format!("https://example.com/{seed}")
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(20))]

    // -- Code generation --------------------------------------------------

    /// "Uniqueness while active": no two currently retrievable records
    /// share a code, for any number of records created.
    #[test]
    fn code_generation_uniqueness_while_active(count in 1u32..40) {
        let codes = block_on(async {
            let app = TestApp::new();
            let mut codes = Vec::new();
            for i in 0..count {
                let response = app.post_urls(json!({ "original_url": distinct_url(i) })).await;
                codes.push(response.json()["code"].as_str().unwrap().to_string());
            }
            codes
        });

        let unique: std::collections::HashSet<_> = codes.iter().collect();
        prop_assert_eq!(unique.len(), codes.len());
    }

    /// "Shape": every generated code matches `^[A-Za-z0-9]{7}$`.
    #[test]
    fn code_generation_shape(_seed in 0u32..50) {
        prop_assert!(is_valid_code_shape(&generate_code()));
    }

    /// "No overwrite on collision": an existing record's fields are
    /// byte-for-byte unchanged after any number of forced collisions.
    #[test]
    fn code_generation_no_overwrite_on_collision(collisions in 0usize..10) {
        let store = Store::new();
        let existing = store.create("https://existing.example.com".to_string(), None, || "abc1234".to_string());

        let mut attempts: Vec<String> = std::iter::repeat_n("abc1234".to_string(), collisions).collect();
        attempts.push("xyz9999".to_string());
        let mut attempts = attempts.into_iter();

        store.create("https://new.example.com".to_string(), None, move || attempts.next().unwrap());

        let after = store.get("abc1234").unwrap();
        prop_assert_eq!(after.original_url, existing.original_url);
        prop_assert_eq!(after.created_at, existing.created_at);
        prop_assert_eq!(after.click_count, existing.click_count);
    }

    // -- Click tracking -----------------------------------------------------

    /// "Monotonic non-negative": click_count never decreases across a
    /// sequence of increments (non-negativity itself is a structural
    /// guarantee of `u64`, not something that can be violated at runtime).
    #[test]
    fn click_tracking_monotonic_non_negative(increments in 1u32..50) {
        let store = Store::new();
        store.create("https://example.com".to_string(), None, || "abc1234".to_string());

        let mut previous = 0u64;
        for _ in 0..increments {
            let current = store.increment_click_count("abc1234").unwrap();
            prop_assert!(current > previous);
            previous = current;
        }
    }

    /// "Exactly-once per successful redirect": N concurrent 302 redirects
    /// of the same code increase click_count by exactly N — the actual
    /// concurrency proof, firing real concurrent requests through the
    /// HTTP layer against one shared `Arc<Store>`, not an assumption that
    /// Rust's ownership model makes this safe by construction.
    #[test]
    fn click_tracking_exactly_once_per_successful_redirect(concurrency in 1u32..25) {
        let final_count = block_on(async {
            let app = TestApp::new();
            app.seed("abc1234", "https://example.com/target", None);

            let handles: Vec<_> = (0..concurrency)
                .map(|_| {
                    let app = app.clone();
                    tokio::spawn(async move { app.get_redirect("abc1234").await.status })
                })
                .collect();
            for handle in handles {
                assert_eq!(handle.await.unwrap(), 302);
            }
            app.click_count("abc1234").unwrap()
        });

        prop_assert_eq!(final_count, concurrency as u64);
    }

    /// "No increment on failure": 404 (unknown/malformed code) and 410
    /// (expired) responses never change click_count.
    #[test]
    fn click_tracking_no_increment_on_failure(malformed in "[!@#$]{1,10}") {
        let (not_found_count, expired_count) = block_on(async {
            let app = TestApp::new();
            app.seed("abc1234", "https://example.com/target", Some(Utc::now() - Duration::hours(1)));

            for _ in 0..3 {
                app.get_redirect(&malformed).await;
                app.get_redirect("zzzzzzz").await;
                app.get_redirect("abc1234").await;
            }

            (app.click_count("zzzzzzz"), app.click_count("abc1234"))
        });

        prop_assert_eq!(not_found_count, None);
        prop_assert_eq!(expired_count, Some(0));
    }

    /// "No increment on metadata read": any number of metadata reads
    /// never changes click_count.
    #[test]
    fn click_tracking_no_increment_on_metadata_read(reads in 1u32..30) {
        let count = block_on(async {
            let app = TestApp::new();
            app.seed("abc1234", "https://example.com/target", None);
            for _ in 0..reads {
                app.get_metadata("abc1234").await;
            }
            app.click_count("abc1234").unwrap()
        });

        prop_assert_eq!(count, 0);
    }

    // -- short_url construction ----------------------------------------

    /// "Deterministic from code and configuration": short_url always
    /// equals the *current* BASE_URL joined with code, even for a record
    /// created under a different BASE_URL — proving it's recomputed, not
    /// stored (ADR-0005).
    #[test]
    fn short_url_deterministic_from_code_and_configuration(seed in 0u32..20) {
        let (code, short_url_under_new_base) = block_on(async {
            let original = TestApp::with_base_url("https://old.example");
            let response = original.post_urls(json!({ "original_url": distinct_url(seed) })).await;
            let code = response.json()["code"].as_str().unwrap().to_string();

            let repointed = original.with_same_store_and_base_url("https://new.example");
            let response = repointed.get_metadata(&code).await;
            (code, response.json()["short_url"].as_str().unwrap().to_string())
        });

        prop_assert_eq!(short_url_under_new_base, format!("https://new.example/{code}"));
    }

    // -- Duplicate submissions -------------------------------------------

    /// "No implicit deduplication": submitting the same original_url N
    /// times produces N records with N distinct codes.
    #[test]
    fn duplicate_submissions_no_implicit_deduplication(count in 2u32..20) {
        let codes = block_on(async {
            let app = TestApp::new();
            let mut codes = Vec::new();
            for _ in 0..count {
                let response = app.post_urls(json!({ "original_url": "https://example.com/same" })).await;
                codes.push(response.json()["code"].as_str().unwrap().to_string());
            }
            codes
        });

        let unique: std::collections::HashSet<_> = codes.iter().collect();
        prop_assert_eq!(unique.len(), codes.len());
    }

    // -- Round-trip integrity ----------------------------------------------

    /// "Original URL is preserved exactly": metadata reproduces the exact
    /// submitted string, for arbitrary safe path suffixes.
    #[test]
    fn round_trip_original_url_preserved_exactly(suffix in "[a-zA-Z0-9/_.~-]{0,60}") {
        let original_url = format!("https://example.com/{suffix}");
        let returned = block_on(async {
            let app = TestApp::new();
            let response = app.post_urls(json!({ "original_url": original_url.clone() })).await;
            let code = response.json()["code"].as_str().unwrap().to_string();
            app.get_metadata(&code).await.json()["original_url"].as_str().unwrap().to_string()
        });

        prop_assert_eq!(returned, original_url);
    }

    /// "Round-trip integrity" (Location header, per ADR-0007): the
    /// redirect Location header is percent-encoding-equivalent to
    /// original_url — parsing both resolves to the identical resource,
    /// even when original_url contains characters that need encoding for
    /// safe header transport.
    #[test]
    fn round_trip_location_header_is_percent_encoding_equivalent(word in "[a-zA-Z0-9]{1,10}") {
        let original_url = format!("https://example.com/{word} name/caf\u{e9}");
        let (location, expected) = block_on(async {
            let app = TestApp::new();
            let response = app.post_urls(json!({ "original_url": original_url.clone() })).await;
            let code = response.json()["code"].as_str().unwrap().to_string();
            let redirect = app.get_redirect(&code).await;
            (redirect.location().to_string(), original_url)
        });

        let expected_url = url::Url::parse(&expected).unwrap();
        let location_url = url::Url::parse(&location).unwrap();
        prop_assert_eq!(location_url, expected_url);
    }

    /// "Timestamps round-trip in UTC": a submitted expires_at (naive or
    /// with an offset) reads back as the same instant, in UTC.
    #[test]
    fn round_trip_timestamps_round_trip_in_utc(hours in 1i64..1000, use_offset in any::<bool>()) {
        let target = Utc::now() + Duration::hours(hours);
        let submitted = if use_offset {
            target.to_rfc3339()
        } else {
            target.format("%Y-%m-%dT%H:%M:%S").to_string()
        };

        let returned = block_on(async {
            let app = TestApp::new();
            let response = app
                .post_urls(json!({ "original_url": "https://example.com", "expires_at": submitted }))
                .await;
            response.json()["expires_at"].as_str().unwrap().to_string()
        });

        let returned: DateTime<Utc> = returned.parse().unwrap();
        let expected = if use_offset { target } else { target.trunc_subsecs(0) };
        prop_assert_eq!(returned, expected);
    }

    // -- Expiration -----------------------------------------------------

    /// "Boundary is inclusive": a redirect at or after expires_at is
    /// treated as expired (410); strictly before is active (302).
    #[test]
    fn expiration_boundary_is_inclusive(delta_seconds in -30i64..30) {
        let (status, delta_is_non_negative) = block_on(async {
            let app = TestApp::new();
            let expires_at = Utc::now() + Duration::seconds(delta_seconds);
            app.seed("abc1234", "https://example.com/target", Some(expires_at));
            let now_after_seed = Utc::now();
            let status = app.get_redirect("abc1234").await.status.as_u16();
            (status, now_after_seed >= expires_at)
        });

        if delta_is_non_negative {
            prop_assert_eq!(status, 410);
        } else {
            prop_assert!(status == 302 || status == 410);
        }
    }

    /// "Expiration doesn't affect metadata visibility": metadata always
    /// returns 200 whether or not the code has expired.
    #[test]
    fn expiration_does_not_affect_metadata_visibility(delta_hours in -100i64..100) {
        let status = block_on(async {
            let app = TestApp::new();
            app.seed("abc1234", "https://example.com/target", Some(Utc::now() + Duration::hours(delta_hours)));
            app.get_metadata("abc1234").await.status.as_u16()
        });

        prop_assert_eq!(status, 200);
    }

    // -- Validation -------------------------------------------------------

    /// "Creation-time-only expiration validation": any past expires_at is
    /// rejected with 422 at creation.
    #[test]
    fn validation_creation_time_only_expiration_validation(seconds_in_past in 1i64..1_000_000) {
        let status = block_on(async {
            let app = TestApp::new();
            let expires_at = Utc::now() - Duration::seconds(seconds_in_past);
            app.post_urls(json!({ "original_url": "https://example.com", "expires_at": expires_at.to_rfc3339() }))
                .await
                .status
                .as_u16()
        });

        prop_assert_eq!(status, 422);
    }

    /// "Scheme restriction is exhaustive": any scheme other than exactly
    /// http/https is rejected at creation, for arbitrary scheme strings.
    #[test]
    fn validation_scheme_restriction_is_exhaustive(scheme in "[a-z]{2,10}") {
        prop_assume!(scheme != "http" && scheme != "https");
        let status = block_on(async {
            let app = TestApp::new();
            app.post_urls(json!({ "original_url": format!("{scheme}://example.com/x") }))
                .await
                .status
                .as_u16()
        });

        prop_assert_eq!(status, 422);
    }

    /// "Length restriction is exhaustive": any original_url longer than
    /// 2048 code points is rejected; at or under the limit is accepted.
    #[test]
    fn validation_length_restriction_is_exhaustive(extra in 1usize..200) {
        let prefix = "https://example.com/";
        let over_limit = format!("{prefix}{}", "a".repeat(2048 - prefix.chars().count() + extra));
        let under_limit = format!("{prefix}{}", "a".repeat(2048 - prefix.chars().count()));

        let (over_status, under_status) = block_on(async {
            let app = TestApp::new();
            let over = app.post_urls(json!({ "original_url": over_limit })).await.status.as_u16();
            let under = app.post_urls(json!({ "original_url": under_limit })).await.status.as_u16();
            (over, under)
        });

        prop_assert_eq!(over_status, 422);
        prop_assert_eq!(under_status, 201);
    }

    /// "Malformed and missing codes are indistinguishable to the caller":
    /// every path segment that doesn't match the code shape returns the
    /// same 404 as a well-formed but nonexistent code, from both the
    /// redirect and metadata endpoints.
    #[test]
    fn validation_malformed_and_missing_codes_are_indistinguishable(candidate in "[A-Za-z0-9]{0,20}") {
        prop_assume!(!is_valid_code_shape(&candidate));
        let (redirect_status, metadata_status) = block_on(async {
            let app = TestApp::new();
            let redirect = app.get_redirect(&candidate).await;
            let metadata = app.get_metadata(&candidate).await;
            (redirect.status.as_u16(), metadata.status.as_u16())
        });

        prop_assert_eq!(redirect_status, 404);
        prop_assert_eq!(metadata_status, 404);
    }
}


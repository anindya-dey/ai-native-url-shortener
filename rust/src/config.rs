//! `BASE_URL` loading and validation — see
//! `blueprint/specs/shared-conventions.md` ("Configuration").

use std::env;

/// Validates that `value` is an absolute `http`/`https` URL with no
/// trailing slash. Returns the validated string unchanged.
pub fn validate_base_url(value: &str) -> Result<String, String> {
    let url = url::Url::parse(value).map_err(|e| format!("BASE_URL is not a valid URL: {e}"))?;
    if url.scheme() != "http" && url.scheme() != "https" {
        return Err("BASE_URL must use http or https".to_string());
    }
    if value.ends_with('/') {
        return Err("BASE_URL must not have a trailing slash".to_string());
    }
    Ok(value.to_string())
}

/// Reads and validates `BASE_URL` from the environment. Fails fast (no
/// default) per `shared-conventions.md`.
pub fn base_url_from_env() -> Result<String, String> {
    let value = env::var("BASE_URL").map_err(|_| "BASE_URL is required and was not set".to_string())?;
    validate_base_url(&value)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_absolute_url_without_trailing_slash() {
        assert!(validate_base_url("https://short.example").is_ok());
    }

    #[test]
    fn rejects_trailing_slash() {
        assert!(validate_base_url("https://short.example/").is_err());
    }

    #[test]
    fn rejects_non_http_scheme() {
        assert!(validate_base_url("ftp://short.example").is_err());
    }

    #[test]
    fn rejects_malformed_url() {
        assert!(validate_base_url("not a url").is_err());
    }
}

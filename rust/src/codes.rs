//! Code shape and generation — shared by URL creation (generates codes)
//! and Redirect/Metadata (validate a path segment's shape before ever
//! looking it up, per ADR-0006). Governed by `blueprint/specs/url-creation.md`
//! and `blueprint/specs/shared-conventions.md` ("Identifiers").

use rand::distributions::Alphanumeric;
use rand::Rng;

pub const CODE_LENGTH: usize = 7;

/// `^[A-Za-z0-9]{7}$` — matches the `Code` parameter pattern in
/// `blueprint/contracts/openapi.yaml`.
pub fn is_valid_code_shape(code: &str) -> bool {
    code.chars().count() == CODE_LENGTH && code.chars().all(|c| c.is_ascii_alphanumeric())
}

/// Generates a random 7-character code from `[A-Za-z0-9]`.
pub fn generate_code() -> String {
    rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(CODE_LENGTH)
        .map(char::from)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generated_code_matches_shape() {
        for _ in 0..100 {
            assert!(is_valid_code_shape(&generate_code()));
        }
    }

    #[test]
    fn rejects_wrong_length() {
        assert!(!is_valid_code_shape("ab"));
        assert!(!is_valid_code_shape("toolongcode123"));
    }

    #[test]
    fn rejects_invalid_characters() {
        assert!(!is_valid_code_shape("abc-123"));
    }
}

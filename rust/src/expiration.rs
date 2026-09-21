//! The expiration rule — cross-cutting per `blueprint/MODULE_BOUNDARIES.md`
//! ("Expiration rule"), not a module of its own. URL creation calls
//! [`is_strictly_future`]; Redirect calls [`is_expired`]. Metadata
//! deliberately calls neither.

use chrono::{DateTime, Utc};

/// `blueprint/specs/expiration.md` ("Boundary condition"): expiry is
/// inclusive of the exact instant — `now >= expires_at` is expired.
pub fn is_expired(expires_at: Option<DateTime<Utc>>, now: DateTime<Utc>) -> bool {
    match expires_at {
        Some(expires_at) => now >= expires_at,
        None => false,
    }
}

/// `blueprint/specs/url-creation.md`: a submitted `expires_at` must be
/// strictly in the future relative to request-processing time.
pub fn is_strictly_future(expires_at: DateTime<Utc>, now: DateTime<Utc>) -> bool {
    expires_at > now
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Duration;

    #[test]
    fn no_expires_at_never_expires() {
        assert!(!is_expired(None, Utc::now()));
    }

    #[test]
    fn boundary_is_inclusive() {
        let now = Utc::now();
        assert!(is_expired(Some(now), now));
    }

    #[test]
    fn past_is_expired_future_is_not() {
        let now = Utc::now();
        assert!(is_expired(Some(now - Duration::hours(1)), now));
        assert!(!is_expired(Some(now + Duration::hours(1)), now));
    }

    #[test]
    fn strictly_future_rejects_now_and_past() {
        let now = Utc::now();
        assert!(!is_strictly_future(now, now));
        assert!(!is_strictly_future(now - Duration::hours(1), now));
        assert!(is_strictly_future(now + Duration::hours(1), now));
    }
}

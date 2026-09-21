//! Timestamp parsing and serialization —
//! `blueprint/specs/shared-conventions.md` ("Time handling"): all
//! timestamps are UTC, ISO 8601; a naive (timezone-less) input is
//! interpreted as UTC.

use chrono::{DateTime, NaiveDateTime, SecondsFormat, Utc};
use serde::Serializer;

/// Parses an `expires_at` string that may carry a timezone offset (RFC
/// 3339) or be naive. A naive value is interpreted as UTC. Returns `None`
/// for anything else — mapped to a `422` by the caller.
pub fn parse_expires_at(value: &str) -> Option<DateTime<Utc>> {
    if let Ok(dt) = DateTime::parse_from_rfc3339(value) {
        return Some(dt.with_timezone(&Utc));
    }
    ["%Y-%m-%dT%H:%M:%S%.f", "%Y-%m-%dT%H:%M:%S"]
        .iter()
        .find_map(|format| NaiveDateTime::parse_from_str(value, format).ok())
        .map(|naive| naive.and_utc())
}

/// Serializes as ISO 8601 UTC with a `Z` suffix, matching
/// `shared-conventions.md`'s example format (e.g.
/// `2026-09-16T12:00:00Z`), preserving whatever sub-second precision the
/// value carries.
pub fn serialize<S: Serializer>(dt: &DateTime<Utc>, serializer: S) -> Result<S::Ok, S::Error> {
    serializer.serialize_str(&dt.to_rfc3339_opts(SecondsFormat::AutoSi, true))
}

pub fn serialize_opt<S: Serializer>(
    dt: &Option<DateTime<Utc>>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    match dt {
        Some(dt) => serialize(dt, serializer),
        None => serializer.serialize_none(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;

    #[test]
    fn parses_naive_timestamp_as_utc() {
        let parsed = parse_expires_at("2026-09-16T12:00:00").unwrap();
        assert_eq!(parsed, Utc.with_ymd_and_hms(2026, 9, 16, 12, 0, 0).unwrap());
    }

    #[test]
    fn parses_timestamp_with_offset() {
        let parsed = parse_expires_at("2026-09-16T14:00:00+02:00").unwrap();
        assert_eq!(parsed, Utc.with_ymd_and_hms(2026, 9, 16, 12, 0, 0).unwrap());
    }

    #[test]
    fn parses_timestamp_with_z_suffix() {
        let parsed = parse_expires_at("2026-09-16T12:00:00Z").unwrap();
        assert_eq!(parsed, Utc.with_ymd_and_hms(2026, 9, 16, 12, 0, 0).unwrap());
    }

    #[test]
    fn rejects_garbage() {
        assert!(parse_expires_at("not a timestamp").is_none());
    }
}

//! In-memory, thread-safe short URL store.
//!
//! Shared infrastructure used by all three modules, but each module has
//! exclusive write authority over a distinct slice per
//! `blueprint/MODULE_BOUNDARIES.md`: URL creation calls [`Store::create`],
//! Redirect calls [`Store::increment_click_count`], and Metadata only ever
//! calls the read-only [`Store::get`].
//!
//! `click_count` increments happen inside a single write-lock acquisition
//! (get_mut + `+= 1`, no intervening unlock/relock), which is what makes
//! the "exactly-once per successful redirect" guarantee in
//! `blueprint/GUARANTEES.md` hold under concurrency — see
//! `tests/guarantees.rs` for a property test that actually fires
//! concurrent requests against this store through the HTTP layer.

use std::collections::HashMap;
use std::sync::RwLock;

use chrono::{DateTime, Utc};

#[derive(Debug, Clone)]
pub struct Record {
    pub code: String,
    pub original_url: String,
    pub click_count: u64,
    pub created_at: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
}

#[derive(Default)]
pub struct Store {
    records: RwLock<HashMap<String, Record>>,
}

impl Store {
    pub fn new() -> Self {
        Self::default()
    }

    /// Creates a new record using `next_code` to generate candidate codes,
    /// retrying on collision without ever touching an existing record
    /// (`blueprint/specs/url-creation.md`, "Code collision is retried, not
    /// overwritten"). `next_code` is injectable so tests can force a
    /// collision deterministically.
    pub fn create(
        &self,
        original_url: String,
        expires_at: Option<DateTime<Utc>>,
        mut next_code: impl FnMut() -> String,
    ) -> Record {
        use std::collections::hash_map::Entry;

        let mut records = self.records.write().unwrap();
        loop {
            let code = next_code();
            if let Entry::Vacant(entry) = records.entry(code.clone()) {
                let record = Record { code, original_url, click_count: 0, created_at: Utc::now(), expires_at };
                entry.insert(record.clone());
                return record;
            }
        }
    }

    pub fn get(&self, code: &str) -> Option<Record> {
        self.records.read().unwrap().get(code).cloned()
    }

    /// Atomically increments `click_count` for `code` and returns the new
    /// value, or `None` if `code` doesn't exist. The increment happens
    /// under one write-lock acquisition — no read-then-write race.
    pub fn increment_click_count(&self, code: &str) -> Option<u64> {
        let mut records = self.records.write().unwrap();
        let record = records.get_mut(code)?;
        record.click_count += 1;
        Some(record.click_count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_returns_a_record_with_zero_clicks() {
        let store = Store::new();
        let record = store.create("https://example.com".to_string(), None, || "abc1234".to_string());
        assert_eq!(record.click_count, 0);
        assert_eq!(record.code, "abc1234");
    }

    #[test]
    fn collision_retries_without_overwriting_existing_record() {
        let store = Store::new();
        store.create("https://existing.example.com".to_string(), None, || "abc1234".to_string());

        let mut attempts = vec!["abc1234".to_string(), "xyz9999".to_string()].into_iter();
        let record = store.create("https://new.example.com".to_string(), None, || attempts.next().unwrap());

        assert_eq!(record.code, "xyz9999");
        let existing = store.get("abc1234").unwrap();
        assert_eq!(existing.original_url, "https://existing.example.com");
    }

    #[test]
    fn increment_click_count_returns_none_for_unknown_code() {
        let store = Store::new();
        assert_eq!(store.increment_click_count("zzzzzzz"), None);
    }
}

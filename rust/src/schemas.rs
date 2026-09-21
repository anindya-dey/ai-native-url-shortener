//! Request/response DTOs mirroring the schemas in
//! `blueprint/contracts/openapi.yaml`.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::timestamps;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CreateUrlRequest {
    pub original_url: Option<String>,
    pub expires_at: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct ShortUrl {
    pub code: String,
    pub original_url: String,
    pub short_url: String,
    pub click_count: u64,
    #[serde(serialize_with = "timestamps::serialize")]
    pub created_at: DateTime<Utc>,
    #[serde(serialize_with = "timestamps::serialize_opt")]
    pub expires_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize)]
pub struct ErrorBody {
    pub detail: String,
}

impl ErrorBody {
    pub fn new(detail: impl Into<String>) -> Self {
        Self { detail: detail.into() }
    }
}

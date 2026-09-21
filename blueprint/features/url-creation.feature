Feature: URL creation
  As an API client
  I want to submit a destination URL
  So that I receive a short, redirectable code

  # Source of truth for these rules: ../specs/url-creation.md

  Scenario: Valid destination creates a short URL
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "https://example.com/a/long/path"
    Then the response status is 201
    And the response body's original_url equals "https://example.com/a/long/path"
    And the response body's code matches "^[A-Za-z0-9]{7}$"
    And the response body's click_count equals 0
    And the response body's expires_at is null

  Scenario: Valid destination with a future expiration
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "https://example.com" and expires_at 1 hour in the future
    Then the response status is 201
    And the response body's expires_at equals the submitted timestamp normalized to UTC

  Scenario: Unsupported scheme is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "ftp://example.com/file"
    Then the response status is 422

  Scenario: Malformed URL is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "not a url"
    Then the response status is 422

  Scenario: Oversized original_url is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with an original_url of 2049 characters
    Then the response status is 422

  Scenario: Length limit counts Unicode code points, not UTF-16 code units
    Given no prior state
    When the client POSTs to /api/v1/urls with an original_url of exactly 2048 Unicode code points, using a character that requires a UTF-16 surrogate pair
    Then the response status is 201
    When the client POSTs to /api/v1/urls with that same original_url plus one more code point (2049 code points)
    Then the response status is 422

  Scenario: Scheme-only URL with no host is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "https://"
    Then the response status is 422

  Scenario: original_url containing control characters is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url containing a carriage return or line feed character
    Then the response status is 422

  Scenario: Missing original_url is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with no original_url
    Then the response status is 422

  Scenario: Past expiration is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "https://example.com" and expires_at 1 hour in the past
    Then the response status is 422

  Scenario: Code collision is retried, not overwritten
    Given an existing short URL record with code "abc1234" and original_url "https://existing.example.com"
    And the code generator is stubbed to produce "abc1234" on its first attempt and a different valid code on retry
    When the client POSTs to /api/v1/urls with original_url "https://new.example.com"
    Then the response status is 201
    And the response body's code does not equal "abc1234"
    And the existing record for code "abc1234" still has original_url "https://existing.example.com"

  Scenario: short_url is built from the configured base URL and the code
    Given the configured BASE_URL is "https://short.example"
    When the client POSTs to /api/v1/urls with original_url "https://example.com"
    Then the response body's short_url matches "^https://short\.example/[A-Za-z0-9]{7}$"
    And the response body's short_url ends with the response body's code

  Scenario: Submitting the same original_url twice creates two independent codes
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "https://example.com/same"
    And the client POSTs to /api/v1/urls with original_url "https://example.com/same" again
    Then both responses have status 201
    And the two responses have different codes

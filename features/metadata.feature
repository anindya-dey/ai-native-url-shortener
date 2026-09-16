Feature: Metadata
  As an API client
  I want to inspect a short URL's data without triggering a redirect
  So that I can build tools around short URLs without affecting click counts

  # Source of truth for these rules: ../../specs/metadata.md

  Scenario: Metadata for an active short URL
    Given an existing, unexpired short URL with code "abc1234"
    And click_count for "abc1234" is 3
    When the client GETs /api/v1/urls/abc1234
    Then the response status is 200
    And the response body matches the ShortUrl schema
    And click_count for "abc1234" is still 3

  Scenario: Metadata for an expired short URL is still retrievable
    Given an existing short URL with code "abc1234" that expired 1 hour ago
    When the client GETs /api/v1/urls/abc1234
    Then the response status is 200
    And the response body's expires_at is in the past

  Scenario: Metadata for unknown code returns 404
    Given no short URL exists with code "zzzzzzz"
    When the client GETs /api/v1/urls/zzzzzzz
    Then the response status is 404
    And the response body's detail equals "Short URL not found"

  Scenario: Metadata lookups never increment click_count
    Given an existing, unexpired short URL with code "abc1234"
    And click_count for "abc1234" is 0
    When the client GETs /api/v1/urls/abc1234 five times in a row
    Then click_count for "abc1234" is still 0

  Scenario: Malformed code returns 404, not 422
    Given no prior state
    When the client GETs /api/v1/urls/ab
    Then the response status is 404

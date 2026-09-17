Feature: Expiration
  As the system
  I need expired short URLs to stop redirecting while remaining inspectable
  So that expiration is enforced consistently across endpoints

  # Source of truth for these rules: ../specs/expiration.md

  Scenario: Redirect to an expired short URL returns 410
    Given an existing short URL with code "abc1234" that expired 1 hour ago
    When the client GETs /abc1234
    Then the response status is 410
    And the response body's detail equals "Short URL has expired"
    And click_count for "abc1234" is unchanged by this request

  Scenario: Redirect at the exact expiration boundary is treated as expired
    Given an existing short URL with code "abc1234" whose expires_at equals the current request time exactly
    When the client GETs /abc1234
    Then the response status is 410

  Scenario: A short URL with no expires_at never expires
    Given an existing short URL with code "abc1234" and no expires_at
    When the client GETs /abc1234
    Then the response status is 302

  Scenario: A naive expires_at at creation is interpreted as UTC
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "https://example.com" and a naive (no timezone) expires_at 1 hour in the future
    Then the response status is 201
    And the response body's expires_at is expressed in UTC with the same instant as submitted

  Scenario: Metadata remains available after expiration
    Given an existing short URL with code "abc1234" that expired 1 hour ago
    When the client GETs /api/v1/urls/abc1234
    Then the response status is 200
    And the response body's expires_at is in the past

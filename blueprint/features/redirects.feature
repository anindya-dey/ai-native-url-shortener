Feature: Redirects
  As a user following a short URL
  I want to be redirected to the original destination
  So that the short URL behaves like the original link

  # Source of truth for these rules: ../specs/redirects.md
  # Expiration-specific scenarios live in expiration.feature.

  Scenario: Redirect to an active short URL
    Given an existing, unexpired short URL with code "abc1234" and original_url "https://example.com/target"
    And click_count for "abc1234" is 0
    When the client GETs /abc1234
    Then the response status is 302
    And the response Location header equals "https://example.com/target"
    And click_count for "abc1234" equals 1

  Scenario: Unknown code returns 404
    Given no short URL exists with code "zzzzzzz"
    When the client GETs /zzzzzzz
    Then the response status is 404
    And the response body's detail equals "Short URL not found"

  Scenario: Repeated redirects accumulate click_count
    Given an existing, unexpired short URL with code "abc1234"
    And click_count for "abc1234" is 5
    When the client GETs /abc1234
    Then click_count for "abc1234" equals 6

  Scenario: Concurrent redirects do not lose click count
    Given an existing, unexpired short URL with code "abc1234"
    And click_count for "abc1234" is 0
    When 10 redirect requests for "abc1234" are made concurrently
    Then click_count for "abc1234" equals 10

  Scenario: A 404 response does not modify click_count
    Given no short URL exists with code "zzzzzzz"
    When the client GETs /zzzzzzz
    Then no click_count is modified as a result of this request

  Scenario: Malformed code returns 404, not 422
    Given no prior state
    When the client GETs /ab
    Then the response status is 404
    And the response body's detail equals "Short URL not found"

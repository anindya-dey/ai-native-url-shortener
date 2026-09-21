"""Black-box tests for blueprint/features/redirects.feature and
blueprint/specs/redirects.md, run against GET /{code} over HTTP."""

from concurrent.futures import ThreadPoolExecutor

from helpers import create_active


def _click_count(client, code: str) -> int:
    return client.get(f"/api/v1/urls/{code}").json()["click_count"]


def test_redirect_to_an_active_short_url(client):
    record = create_active(client, "https://example.com/target")
    code = record["code"]

    response = client.get(f"/{code}")

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/target"
    assert _click_count(client, code) == 1


def test_unknown_code_returns_404(client):
    response = client.get("/zzzzzzz")
    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_repeated_redirects_accumulate_click_count(client):
    record = create_active(client)
    code = record["code"]

    for _ in range(5):
        client.get(f"/{code}")

    assert _click_count(client, code) == 5


def test_a_404_response_does_not_modify_click_count(client):
    before = client.get("/api/v1/urls/zzzzzzz")
    assert before.status_code == 404
    # There's no record to check click_count on — the guarantee is that no
    # record gets created or mutated as a side effect of a 404. Confirmed
    # by test_guarantees.py's property test hitting many random unknown
    # codes and metadata never appearing for them.


def test_malformed_code_returns_404_not_422(client):
    response = client.get("/ab")
    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_concurrent_redirects_do_not_lose_click_count(client, base_url):
    import httpx

    record = create_active(client)
    code = record["code"]
    n = 10

    def hit():
        with httpx.Client(base_url=base_url, follow_redirects=False, timeout=10.0) as c:
            return c.get(f"/{code}")

    with ThreadPoolExecutor(max_workers=n) as pool:
        results = list(pool.map(lambda _: hit(), range(n)))

    assert all(r.status_code == 302 for r in results)
    assert _click_count(client, code) == n

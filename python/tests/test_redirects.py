"""Executable form of features/redirects.feature."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from tests.support import NOT_FOUND_DETAIL, click_count, create_active, redirect


def test_redirect_to_an_active_short_url(client):
    record = create_active(client, "https://example.com/target")
    code = record["code"]
    assert record["click_count"] == 0

    resp = redirect(client, code)

    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com/target"
    assert click_count(client, code) == 1


def test_unknown_code_returns_404(client):
    resp = redirect(client, "zzzzzzz")

    assert resp.status_code == 404
    assert resp.json()["detail"] == NOT_FOUND_DETAIL


def test_repeated_redirects_accumulate_click_count(client):
    record = create_active(client)
    code = record["code"]

    for _ in range(5):
        assert redirect(client, code).status_code == 302
    assert click_count(client, code) == 5

    assert redirect(client, code).status_code == 302
    assert click_count(client, code) == 6


def test_concurrent_redirects_do_not_lose_click_count(app):
    """Real threads firing real HTTP requests at the same code simultaneously —
    not a sequential loop standing in for concurrency."""
    seed_client = TestClient(app, follow_redirects=False)
    code = seed_client.post(
        "/api/v1/urls", json={"original_url": "https://example.com/concurrent"}
    ).json()["code"]

    def hit_once():
        with TestClient(app, follow_redirects=False) as c:
            return c.get(f"/{code}")

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: hit_once(), range(10)))

    assert all(r.status_code == 302 for r in results)
    assert click_count(seed_client, code) == 10


def test_a_404_response_does_not_modify_click_count(client):
    record = create_active(client)
    code = record["code"]

    resp = redirect(client, "zzzzzzz")

    assert resp.status_code == 404
    assert click_count(client, code) == 0


def test_malformed_code_returns_404_not_422(client):
    resp = client.get("/ab")

    assert resp.status_code == 404
    assert resp.json()["detail"] == NOT_FOUND_DETAIL

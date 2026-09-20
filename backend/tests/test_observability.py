from fastapi.testclient import TestClient

from app.retrieval.cache import SearchCache


def test_cache_keys_are_stable_and_user_scoped() -> None:
    first = SearchCache.key("user-a", {"query": "risk", "limit": 8})
    reordered = SearchCache.key("user-a", {"limit": 8, "query": "risk"})
    other_user = SearchCache.key("user-b", {"query": "risk", "limit": 8})
    assert first == reordered
    assert first != other_user


def test_prometheus_metrics_endpoint(client: TestClient) -> None:
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "document_search_http_requests_total" in response.text
    assert "document_search_ingestion_queue_depth" in response.text

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_returns_results_with_supplier_ids():
    response = client.post(
        "/search",
        json={
            "query": "Find ISO-certified copper cable suppliers in Vietnam, India, or China supplying large US companies in the last 12 months with no compliance concerns"
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_query"]["category"] == "copper cable"
    assert payload["results"]
    assert all("supplier_id" in item for item in payload["results"])
    assert "confidence_components" in payload["results"][0]
    assert "source_reliability" in payload["results"][0]["confidence_components"]


def test_supplier_detail_returns_evidence():
    response = client.get("/suppliers/sup_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_name"] == "ABC Cable Vietnam"
    assert payload["evidence"]

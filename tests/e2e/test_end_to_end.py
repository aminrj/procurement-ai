"""End-to-end tests using a running API, DB, and LLM."""

import time
from typing import Any

import httpx
import pytest

API_BASE_URL = "http://localhost:8000"
API_KEY = "test-org-key"
MAX_WAIT_TIME = 60
POLL_INTERVAL = 2


@pytest.fixture(scope="module")
def api_client():
    return httpx.Client(
        base_url=API_BASE_URL,
        headers={"X-API-Key": API_KEY},
        timeout=30.0,
    )


@pytest.fixture(scope="module")
def check_prerequisites(api_client):
    try:
        response = api_client.get("/health")
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        pytest.skip(
            "Prerequisites not met. Ensure API, database, and LLM are running. "
            f"Error: {exc}"
        )


def wait_for_processing(api_client: httpx.Client, tender_id: int) -> dict[str, Any]:
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        response = api_client.get(f"/api/v1/tenders/{tender_id}")
        response.raise_for_status()
        payload = response.json()

        status = payload["status"]
        print(f"status={status}")

        if status in {"complete", "error", "filtered_out", "rated_low"}:
            return payload

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Tender {tender_id} processing timeout after {MAX_WAIT_TIME}s")


@pytest.mark.e2e
def test_full_workflow_with_suitable_tender(api_client, check_prerequisites):
    tender_data = {
        "title": "Cloud Infrastructure Modernization",
        "description": (
            "Seeking a vendor to modernize on-prem infrastructure to cloud-native "
            "architecture with Kubernetes and CI/CD automation."
        ),
        "organization_name": "Test Government Agency",
        "deadline": "2026-03-15",
        "estimated_value": "EUR 625000",
    }

    response = api_client.post("/api/v1/analyze", json=tender_data)
    assert response.status_code == 202

    submitted = response.json()
    tender_id = submitted["tender"]["id"]
    assert submitted["status"] == "processing"

    analyzed = wait_for_processing(api_client, tender_id)
    assert analyzed["status"] in {"complete", "rated_low", "filtered_out"}

    assert analyzed["filter_result"] is not None
    assert isinstance(analyzed["filter_result"]["is_relevant"], bool)

    if analyzed["rating_result"]:
        assert 0 <= analyzed["rating_result"]["overall_score"] <= 10


@pytest.mark.e2e
def test_unsuitable_tender_filtering(api_client, check_prerequisites):
    tender_data = {
        "title": "Construction of Highway Bridge",
        "description": (
            "Construction project for a new bridge requiring civil engineering and "
            "heavy equipment. No software or AI scope."
        ),
        "organization_name": "Transport Authority",
        "deadline": "2026-06-30",
        "estimated_value": "EUR 5000000",
    }

    response = api_client.post("/api/v1/analyze", json=tender_data)
    assert response.status_code == 202

    tender_id = response.json()["tender"]["id"]
    analyzed = wait_for_processing(api_client, tender_id)

    assert analyzed["filter_result"] is not None
    assert analyzed["filter_result"]["is_relevant"] is False


@pytest.mark.e2e
def test_pagination_and_listing(api_client, check_prerequisites):
    response = api_client.get("/api/v1/tenders?page=1&page_size=10")
    assert response.status_code == 200

    payload = response.json()
    assert "tenders" in payload
    assert "total" in payload
    assert payload["page"] == 1


@pytest.mark.e2e
def test_api_error_handling(api_client, check_prerequisites):
    invalid_data = {"title": "Test"}
    response = api_client.post("/api/v1/analyze", json=invalid_data)
    assert response.status_code == 422

    response = api_client.get("/api/v1/tenders/999999")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

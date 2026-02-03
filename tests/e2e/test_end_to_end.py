"""
End-to-end tests using local LLM.

Prerequisites:
1. API server running: uvicorn procurement_ai.api.main:app --reload
2. PostgreSQL running: docker-compose up -d db
3. Local LLM running: LM Studio on http://localhost:1234

Run with: pytest tests/e2e/ -v -s
"""
import time
import httpx
import pytest
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000"
API_KEY = "test-org"
MAX_WAIT_TIME = 60  # seconds
POLL_INTERVAL = 2  # seconds


@pytest.fixture(scope="module")
def api_client():
    """HTTP client for API calls."""
    return httpx.Client(
        base_url=API_BASE_URL,
        headers={"X-API-Key": API_KEY},
        timeout=30.0
    )


@pytest.fixture(scope="module")
def check_prerequisites(api_client):
    """Verify API and LLM are running before tests."""
    try:
        response = api_client.get("/health")
        response.raise_for_status()
        health = response.json()
        
        assert health["status"] == "healthy", "API not healthy"
        assert health["database"] == "healthy", "Database not healthy"
        assert health["llm"] == "configured", "LLM not configured"
        
        print(f"\n✓ Prerequisites check passed")
        return health
    except Exception as e:
        pytest.skip(
            f"Prerequisites not met. Ensure:\n"
            f"1. API running: uvicorn procurement_ai.api.main:app --reload\n"
            f"2. Database: docker-compose up -d db\n"
            f"3. LLM: LM Studio on http://localhost:1234\n"
            f"Error: {e}"
        )


def wait_for_processing(api_client: httpx.Client, tender_id: int) -> Dict[str, Any]:
    """Poll tender status until complete or timeout."""
    start_time = time.time()
    
    while time.time() - start_time < MAX_WAIT_TIME:
        response = api_client.get(f"/api/v1/tenders/{tender_id}")
        response.raise_for_status()
        tender = response.json()
        
        status = tender["status"]
        print(f"  Status: {status}")
        
        if status in ["completed", "failed", "error"]:
            return tender
            
        time.sleep(POLL_INTERVAL)
    
    raise TimeoutError(f"Tender {tender_id} processing timeout after {MAX_WAIT_TIME}s")


@pytest.mark.e2e
def test_full_workflow_with_suitable_tender(api_client, check_prerequisites):
    """
    E2E test: Submit suitable tender → process with LLM → validate results.
    
    This validates the complete workflow including real LLM calls.
    """
    tender_data = {
        "title": "Cloud Infrastructure Modernization",
        "description": """
        We are seeking a vendor to modernize our on-premises infrastructure to cloud-native 
        solutions. The project includes migrating 50+ applications to AWS or Azure, 
        implementing container orchestration with Kubernetes, and setting up CI/CD pipelines.
        
        Requirements:
        - 5+ years cloud migration experience
        - Certified cloud architects (AWS/Azure)
        - Experience with Kubernetes and Docker
        - DevOps automation expertise
        - 24/7 support during migration
        
        Budget: €500,000 - €750,000
        Timeline: 12 months
        """,
        "cpv_codes": ["72000000"],
        "deadline": "2026-03-15T23:59:59",
        "estimated_value": 625000.0,
        "buyer_name": "Test Government Agency"
    }
    
    print("\n1. Submitting tender for analysis...")
    response = api_client.post("/api/v1/tenders/analyze", json=tender_data)
    assert response.status_code == 202
    
    result = response.json()
    tender_id = result["tender_id"]
    assert tender_id > 0
    assert result["status"] == "processing"
    print(f"✓ Tender submitted: ID={tender_id}")
    
    print(f"\n2. Waiting for LLM processing (max {MAX_WAIT_TIME}s)...")
    tender = wait_for_processing(api_client, tender_id)
    
    assert tender["status"] == "completed", f"Processing failed: {tender.get('error')}"
    print("✓ Processing completed")
    
    print("\n3. Validating analysis results...")
    
    # Validate structure
    assert tender["id"] == tender_id
    assert tender["title"] == tender_data["title"]
    
    # Validate filter result
    filter_result = tender.get("filter_result")
    assert filter_result is not None, "Missing filter result"
    assert isinstance(filter_result["is_suitable"], bool)
    assert len(filter_result["reasoning"]) > 20
    print(f"  Filter: suitable={filter_result['is_suitable']}")
    
    # Validate rating result
    rating_result = tender.get("rating_result")
    assert rating_result is not None, "Missing rating result"
    assert 0 <= rating_result["overall_score"] <= 100
    assert len(rating_result["key_strengths"]) > 0
    print(f"  Rating: {rating_result['overall_score']}/100")
    
    # Validate bid document
    bid_docs = tender.get("bid_documents", [])
    assert len(bid_docs) > 0, "No bid documents generated"
    assert len(bid_docs[0]["content"]) > 100
    print(f"  Bid document: {len(bid_docs[0]['content'])} chars")
    
    print("\n✓ All validations passed")


@pytest.mark.e2e
def test_unsuitable_tender_filtering(api_client, check_prerequisites):
    """
    E2E test: Submit unsuitable tender → verify filter rejects it.
    
    Tests that the filter agent correctly identifies mismatches.
    """
    tender_data = {
        "title": "Construction of Highway Bridge",
        "description": """
        Construction project for a new 2km highway bridge. Requires:
        - Civil engineering expertise
        - Heavy construction equipment
        - Concrete and steel materials
        - Bridge construction experience
        
        This is a physical infrastructure project with no IT component.
        """,
        "cpv_codes": ["45221111"],
        "deadline": "2026-06-30T23:59:59",
        "estimated_value": 5000000.0,
        "buyer_name": "Transport Authority"
    }
    
    print("\n1. Submitting unsuitable tender...")
    response = api_client.post("/api/v1/tenders/analyze", json=tender_data)
    assert response.status_code == 202
    
    tender_id = response.json()["tender_id"]
    print(f"✓ Tender submitted: ID={tender_id}")
    
    print("\n2. Waiting for processing...")
    tender = wait_for_processing(api_client, tender_id)
    
    assert tender["status"] == "completed"
    print("✓ Processing completed")
    
    print("\n3. Validating filter decision...")
    filter_result = tender["filter_result"]
    
    assert filter_result["is_suitable"] == False, "Should filter out construction tender"
    assert len(filter_result["reasoning"]) > 20
    print(f"  Correctly filtered as unsuitable")
    
    print("\n✓ Filtering validation passed")


@pytest.mark.e2e
def test_pagination_and_listing(api_client, check_prerequisites):
    """E2E test: Verify tender list endpoint returns processed tenders."""
    print("\n1. Fetching tender list...")
    response = api_client.get("/api/v1/tenders?limit=10&offset=0")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 0
    
    print(f"✓ Found {data['total']} total tenders")
    print("✓ Pagination validation passed")


@pytest.mark.e2e  
def test_api_error_handling(api_client, check_prerequisites):
    """E2E test: Verify proper error responses."""
    print("\n1. Testing invalid input...")
    
    invalid_data = {"title": "Test"}  # Missing required 'description'
    response = api_client.post("/api/v1/tenders/analyze", json=invalid_data)
    assert response.status_code == 422
    print("✓ Got expected 422 validation error")
    
    print("\n2. Testing non-existent tender...")
    response = api_client.get("/api/v1/tenders/999999")
    assert response.status_code == 404
    print("✓ Got expected 404 not found")
    
    print("\n✓ Error handling validation passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

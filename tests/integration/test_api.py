"""
API Integration Tests
Tests the full API endpoints with real database
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from procurement_ai.api.main import app
from procurement_ai.storage import DatabaseManager
from procurement_ai.storage.models import SubscriptionTier, TenderStatus
from procurement_ai.storage.repositories import OrganizationRepository
from procurement_ai.models import TenderCategory


@pytest.fixture
def db():
    """In-memory test database"""
    db = DatabaseManager(database_url="sqlite:///:memory:")
    db.create_all()
    yield db
    db.drop_all()


@pytest.fixture
def test_org(db):
    """Create test organization"""
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        org = org_repo.create(
            name="Test Organization",
            slug="test-org",
            subscription_tier=SubscriptionTier.PRO,
        )
        # Store slug before session closes
        org_slug = org.slug
        org_id = org.id
        
    # Return dict instead of detached object
    return {"slug": org_slug, "id": org_id}


@pytest.fixture
def client(db, test_org):
    """FastAPI test client with mocked database"""
    from procurement_ai.api.dependencies import get_db

    # Override dependency
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def api_headers(test_org):
    """API authentication headers"""
    return {"X-API-Key": test_org["slug"]}


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health endpoint returns status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data


class TestAnalyzeEndpoint:
    """Test tender analysis endpoint"""

    def test_analyze_tender_success(self, client, api_headers):
        """Test successful tender submission"""
        # Don't mock orchestrator - just test the API response
        # Background task will be tested separately
        
        response = client.post(
            "/api/v1/analyze",
            json={
                "title": "AI Cybersecurity Platform",
                "description": "Government needs AI-based threat detection system",
                "organization_name": "National Cyber Agency",
                "deadline": "2026-06-30",
                "estimated_value": "€2,500,000",
            },
            headers=api_headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "processing"
        assert data["tender"]["title"] == "AI Cybersecurity Platform"

    def test_analyze_without_auth(self, client):
        """Test analyze endpoint requires authentication"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "title": "Test Tender",
                "description": "Test description that is long enough",
                "organization_name": "Test Org",
            },
        )

        assert response.status_code == 422  # Missing header

    def test_analyze_with_invalid_api_key(self, client):
        """Test analyze endpoint with invalid API key"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "title": "Test Tender",
                "description": "Test description that is long enough",
                "organization_name": "Test Org",
            },
            headers={"X-API-Key": "invalid-key"},
        )

        assert response.status_code == 401

    def test_analyze_validates_input(self, client, api_headers):
        """Test input validation"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "title": "",  # Too short
                "description": "Short",  # Too short
                "organization_name": "Test",
            },
            headers=api_headers,
        )

        assert response.status_code == 422


class TestListTendersEndpoint:
    """Test tender listing endpoint"""

    def test_list_tenders_empty(self, client, api_headers):
        """Test listing tenders when none exist"""
        response = client.get("/api/v1/tenders", headers=api_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["tenders"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_tenders_with_pagination(self, client, api_headers, db, test_org):
        """Test pagination works"""
        # Create some tenders
        from procurement_ai.storage.repositories import TenderRepository

        with db.get_session() as session:
            tender_repo = TenderRepository(session)
            for i in range(5):
                tender_repo.create(
                    organization_id=test_org["id"],
                    title=f"Tender {i}",
                    description="Test description",
                    organization_name="Test Org",
                    external_id=f"TEST-{i}",
                )

        # Get first page
        response = client.get(
            "/api/v1/tenders?page=1&page_size=2", headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tenders"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3


class TestGetTenderEndpoint:
    """Test get specific tender endpoint"""

    def test_get_tender_not_found(self, client, api_headers):
        """Test getting non-existent tender"""
        response = client.get("/api/v1/tenders/99999", headers=api_headers)  # Use integer ID

        assert response.status_code == 404

    def test_get_tender_success(self, client, api_headers, db, test_org):
        """Test getting tender with analysis"""
        from procurement_ai.storage.repositories import (
            TenderRepository,
            AnalysisRepository,
        )

        # Create tender
        with db.get_session() as session:
            tender_repo = TenderRepository(session)
            tender = tender_repo.create(
                organization_id=test_org["id"],
                title="Test Tender",
                description="Test description",
                organization_name="Test Org",
                external_id="TEST-001",
            )

            # Create analysis
            analysis_repo = AnalysisRepository(session)
            analysis_repo.create(
                tender_id=tender.id,
                is_relevant=True,
                confidence=0.95,
                filter_categories=["cybersecurity", "ai"],
                filter_reasoning="Strong alignment",
                overall_score=8.5,
                strategic_fit=9.0,
                win_probability=8.0,
                strengths=["Good fit"],
                risks=["Timeline tight"],
                recommendation="Pursue",
            )

            tender_id = tender.id

        # Get tender
        response = client.get(f"/api/v1/tenders/{tender_id}", headers=api_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["tender"]["title"] == "Test Tender"
        assert data["filter_result"]["is_relevant"] is True
        assert data["rating_result"]["overall_score"] == 8.5


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root(self, client):
        """Test root endpoint redirects to web UI"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [307, 302, 303]
        assert "/web/" in response.headers["location"]

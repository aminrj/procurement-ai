"""
Integration tests using real PostgreSQL database.
Tests full workflows and database interactions.
"""
import pytest
import os
from src.procurement_ai.storage.database import Database, Base
from src.procurement_ai.storage.repositories import (
    OrganizationRepository,
    TenderRepository,
    AnalysisRepository,
)


# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.slow]


@pytest.fixture(scope="module")
def postgres_db():
    """
    Use real PostgreSQL for integration tests.
    Requires docker-compose to be running.
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@127.0.0.1:5432/procurement_ai?gssencmode=disable"
    )

    db = Database(db_url)

    # Check if database is available
    try:
        with db.get_session() as session:
            session.execute("SELECT 1")
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")

    yield db

    # Cleanup: truncate tables but keep schema
    with db.get_session() as session:
        session.execute("TRUNCATE organizations, users, tenders, analysis_results, bid_documents CASCADE")
        session.commit()


@pytest.fixture
def postgres_session(postgres_db):
    """Provides a PostgreSQL session"""
    with postgres_db.get_session() as session:
        yield session


class TestFullWorkflow:
    """Test complete workflows with real database"""

    def test_multi_tenant_organization_workflow(self, postgres_session):
        """Test creating multiple organizations with data isolation"""
        org_repo = OrganizationRepository(postgres_session)
        tender_repo = TenderRepository(postgres_session)

        # Create two organizations
        org1 = org_repo.create(name="Company A", slug="company-a", subscription_tier="PRO")
        org2 = org_repo.create(name="Company B", slug="company-b", subscription_tier="BASIC")

        # Create tenders for each
        tender1 = tender_repo.create(
            organization_id=org1.id,
            external_id="ORG1-001",
            source="manual",
            title="Org 1 Tender",
        )
        tender2 = tender_repo.create(
            organization_id=org2.id,
            external_id="ORG2-001",
            source="manual",
            title="Org 2 Tender",
        )

        # Verify isolation
        org1_tenders = tender_repo.get_by_organization(org1.id)
        org2_tenders = tender_repo.get_by_organization(org2.id)

        assert len(org1_tenders) == 1
        assert len(org2_tenders) == 1
        assert org1_tenders[0].id == tender1.id
        assert org2_tenders[0].id == tender2.id

    def test_tender_analysis_workflow(self, postgres_session):
        """Test complete tender → analysis workflow"""
        org_repo = OrganizationRepository(postgres_session)
        tender_repo = TenderRepository(postgres_session)
        analysis_repo = AnalysisRepository(postgres_session)

        # Create organization and tender
        org = org_repo.create(name="Test Org", slug="test-org")
        tender = tender_repo.create(
            organization_id=org.id,
            external_id="TEST-001",
            source="manual",
            title="Test Tender",
            status="PENDING",
        )

        # Update to processing
        tender_repo.update_status(tender.id, "PROCESSING")

        # Create analysis
        analysis = analysis_repo.create(
            tender_id=tender.id,
            filter_result={"is_relevant": True, "confidence": 0.9},
            rating_result={"score": 85, "reasoning": "Good match"},
        )

        # Update to completed
        tender_repo.update_status(tender.id, "COMPLETED")

        # Verify
        final_tender = tender_repo.get_by_id(tender.id)
        tender_analyses = analysis_repo.get_by_tender(tender.id)

        assert final_tender.status.value == "COMPLETED"
        assert len(tender_analyses) == 1
        assert tender_analyses[0].filter_result["is_relevant"] is True

    def test_usage_tracking_workflow(self, postgres_session):
        """Test organization usage tracking"""
        org_repo = OrganizationRepository(postgres_session)

        org = org_repo.create(
            name="Limited Org",
            slug="limited-org",
            subscription_tier="BASIC",
        )

        # Initially can analyze
        assert org_repo.can_analyze(org.id) is True

        # Increment counter
        for _ in range(org.monthly_analysis_limit):
            org_repo.increment_analysis_count(org.id)

        # Now at limit
        assert org_repo.can_analyze(org.id) is False

        # Verify counter
        org = org_repo.get_by_id(org.id)
        assert org.monthly_analysis_count == org.monthly_analysis_limit


class TestDatabaseFeatures:
    """Test PostgreSQL-specific features"""

    def test_json_field_storage_and_query(self, postgres_session):
        """Test storing and querying JSON fields"""
        tender_repo = TenderRepository(postgres_session)
        org_repo = OrganizationRepository(postgres_session)

        org = org_repo.create(name="Test", slug="test")
        tender = tender_repo.create(
            organization_id=org.id,
            external_id="JSON-001",
            source="manual",
            title="JSON Test",
        )

        # Store JSON in categories field
        tender.categories = {"primary": "CYBERSECURITY", "secondary": ["AI", "SOFTWARE"]}
        postgres_session.commit()

        # Retrieve and verify
        retrieved = tender_repo.get_by_id(tender.id)
        assert retrieved.categories["primary"] == "CYBERSECURITY"
        assert "AI" in retrieved.categories["secondary"]

    def test_index_performance_on_large_dataset(self, postgres_session):
        """Test that indexes work on larger datasets"""
        org_repo = OrganizationRepository(postgres_session)
        tender_repo = TenderRepository(postgres_session)

        org = org_repo.create(name="Perf Test", slug="perf-test")

        # Create 100 tenders
        for i in range(100):
            tender_repo.create(
                organization_id=org.id,
                external_id=f"PERF-{i:03d}",
                source="manual",
                title=f"Tender {i}",
                status="PENDING" if i % 2 == 0 else "COMPLETED",
            )

        # Query should be fast due to indexes
        pending = tender_repo.get_by_status(org.id, "PENDING")
        completed = tender_repo.get_by_status(org.id, "COMPLETED")

        assert len(pending) == 50
        assert len(completed) == 50

    def test_concurrent_access_safety(self, postgres_db):
        """Test that concurrent sessions don't conflict"""
        org_repo1 = None
        org_repo2 = None

        with postgres_db.get_session() as session1:
            org_repo1 = OrganizationRepository(session1)
            org1 = org_repo1.create(name="Org 1", slug="concurrent-1")

            with postgres_db.get_session() as session2:
                org_repo2 = OrganizationRepository(session2)
                org2 = org_repo2.create(name="Org 2", slug="concurrent-2")

                # Both should succeed
                assert org1.id != org2.id

        # Both should be committed
        with postgres_db.get_session() as session:
            org_repo = OrganizationRepository(session)
            assert org_repo.get_by_slug("concurrent-1") is not None
            assert org_repo.get_by_slug("concurrent-2") is not None

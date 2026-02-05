"""Integration workflow tests against PostgreSQL."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from procurement_ai.storage.database import Database
from procurement_ai.storage.models import SubscriptionTier, TenderStatus
from procurement_ai.storage.repositories import (
    AnalysisRepository,
    OrganizationRepository,
    TenderRepository,
)

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def _suffix() -> str:
    return uuid4().hex[:8]


@pytest.fixture(scope="module")
def postgres_db():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://procurement:procurement@127.0.0.1:5432/procurement",
    )
    db = Database(db_url)

    try:
        with db.get_session() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL not available: {exc}")

    yield db

    with db.get_session() as session:
        session.execute(text("TRUNCATE organizations, users, tenders, analysis_results, bid_documents CASCADE"))


@pytest.fixture
def postgres_session(postgres_db):
    with postgres_db.get_session() as session:
        yield session


class TestFullWorkflow:
    def test_multi_tenant_tender_isolation(self, postgres_session):
        org_repo = OrganizationRepository(postgres_session)
        tender_repo = TenderRepository(postgres_session)
        token = _suffix()

        org1 = org_repo.create(
            name="Company A",
            slug=f"it-company-a-{token}",
            subscription_tier=SubscriptionTier.PRO,
        )
        org2 = org_repo.create(
            name="Company B",
            slug=f"it-company-b-{token}",
            subscription_tier=SubscriptionTier.BASIC,
        )

        tender_repo.create(
            organization_id=org1.id,
            external_id=f"IT-ORG1-{token}",
            source="manual",
            title="Org 1 Tender",
            description="Description 1",
            organization_name="Org 1",
        )
        tender_repo.create(
            organization_id=org2.id,
            external_id=f"IT-ORG2-{token}",
            source="manual",
            title="Org 2 Tender",
            description="Description 2",
            organization_name="Org 2",
        )

        org1_tenders = tender_repo.list_by_organization(org1.id)
        org2_tenders = tender_repo.list_by_organization(org2.id)

        assert len(org1_tenders) == 1
        assert len(org2_tenders) == 1
        assert org1_tenders[0].organization_id == org1.id
        assert org2_tenders[0].organization_id == org2.id

    def test_tender_analysis_workflow(self, postgres_session):
        org_repo = OrganizationRepository(postgres_session)
        tender_repo = TenderRepository(postgres_session)
        analysis_repo = AnalysisRepository(postgres_session)
        token = _suffix()

        org = org_repo.create(name="Test Org", slug=f"it-test-org-{token}")
        tender = tender_repo.create(
            organization_id=org.id,
            external_id=f"IT-TEST-{token}",
            source="manual",
            title="Test Tender",
            description="Test description",
            organization_name="Test Org",
            status=TenderStatus.PENDING,
        )

        tender_repo.update_status(tender.id, TenderStatus.PROCESSING)
        analysis_repo.upsert(
            tender_id=tender.id,
            is_relevant=True,
            confidence=0.9,
            filter_categories=["ai"],
            filter_reasoning="Good fit",
            overall_score=8.0,
            strategic_fit=8.5,
            win_probability=7.5,
            recommendation="Pursue",
        )
        tender_repo.update_status(tender.id, TenderStatus.COMPLETE, processing_time=12.3)

        final_tender = tender_repo.get_by_id(tender.id, org.id)
        analysis = analysis_repo.get_by_tender_id(tender.id)

        assert final_tender is not None
        assert final_tender.status == TenderStatus.COMPLETE
        assert final_tender.processing_time == 12.3
        assert analysis is not None
        assert analysis.is_relevant is True
        assert analysis.overall_score == 8.0

    def test_usage_tracking_workflow(self, postgres_session):
        org_repo = OrganizationRepository(postgres_session)
        org = org_repo.create(name="Limited Org", slug=f"it-limited-org-{_suffix()}")

        assert org_repo.can_analyze(org.id) is True

        for _ in range(org.monthly_analysis_limit):
            org_repo.update_usage(org.id)

        assert org_repo.can_analyze(org.id) is False

        updated = org_repo.get_by_id(org.id)
        assert updated is not None
        assert updated.monthly_analysis_count == updated.monthly_analysis_limit

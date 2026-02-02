"""
Tests for storage repositories using SQLite in-memory database.
Fast unit tests with no external dependencies.
"""
import pytest
from datetime import datetime

from src.procurement_ai.storage.models import SubscriptionTier, UserRole, TenderStatus


class TestOrganizationRepository:
    """Test OrganizationRepository operations"""

    def test_create_organization(self, org_repo):
        """Test creating an organization"""
        org = org_repo.create(
            name="Acme Corp",
            slug="acme-corp",
            subscription_tier=SubscriptionTier.PRO,
        )

        assert org.id is not None
        assert org.name == "Acme Corp"
        assert org.slug == "acme-corp"
        assert org.subscription_tier == SubscriptionTier.PRO
        assert org.monthly_analysis_count == 0
        assert org.is_active is True
        assert org.is_deleted is False

    def test_get_by_id(self, org_repo, sample_organization):
        """Test retrieving organization by ID"""
        org = org_repo.get_by_id(sample_organization.id)

        assert org is not None
        assert org.id == sample_organization.id
        assert org.name == sample_organization.name

    def test_get_by_id_not_found(self, org_repo):
        """Test retrieving non-existent organization"""
        org = org_repo.get_by_id(99999)
        assert org is None

    def test_get_by_slug(self, org_repo, sample_organization):
        """Test retrieving organization by slug"""
        org = org_repo.get_by_slug("test-org")

        assert org is not None
        assert org.slug == "test-org"
        assert org.id == sample_organization.id

    def test_list_all(self, org_repo):
        """Test listing all organizations"""
        # Create multiple organizations
        org_repo.create(name="Org 1", slug="org-1")
        org_repo.create(name="Org 2", slug="org-2")
        org_repo.create(name="Org 3", slug="org-3")

        orgs = org_repo.list_active()
        assert len(orgs) == 3

    def test_soft_delete(self, org_repo, sample_organization):
        """Test soft deleting an organization"""
        result = org_repo.soft_delete(sample_organization.id)
        assert result is True

    def test_increment_analysis_count(self, org_repo, sample_organization):
        """Test incrementing analysis counter"""
        initial_count = sample_organization.monthly_analysis_count

        org_repo.update_usage(sample_organization.id)

        org = org_repo.get_by_id(sample_organization.id)
        assert org.monthly_analysis_count == initial_count + 1

    def test_can_analyze_within_limit(self, org_repo, sample_organization):
        """Test analysis limit check when under limit"""
        assert org_repo.can_analyze(sample_organization.id) is True

    def test_can_analyze_at_limit(self, org_repo, sample_organization):
        """Test analysis limit check when at limit"""
        # Set count to limit
        sample_organization.monthly_analysis_count = sample_organization.monthly_analysis_limit

        assert org_repo.can_analyze(sample_organization.id) is False


class TestUserRepository:
    """Test UserRepository operations"""

    def test_create_user(self, user_repo, sample_organization):
        """Test creating a user"""
        user = user_repo.create(
            organization_id=sample_organization.id,
            email="alice@example.com",
            hashed_password="hashed_pw",
            full_name="Alice Admin",
            role=UserRole.ADMIN,
        )

        assert user.id is not None
        assert user.email == "alice@example.com"
        assert user.full_name == "Alice Admin"
        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.is_verified is False

    def test_get_by_email(self, user_repo, sample_user):
        """Test retrieving user by email"""
        user = user_repo.get_by_email("test@example.com")

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == "test@example.com"

    def test_get_by_email_case_insensitive(self, user_repo, sample_user):
        """Test email lookup is case-insensitive"""
        user = user_repo.get_by_email("TEST@EXAMPLE.COM")

        assert user is not None
        assert user.email == "test@example.com"

    def test_get_by_organization(self, user_repo, sample_organization):
        """Test retrieving users by organization"""
        # Create multiple users
        user_repo.create(
            organization_id=sample_organization.id,
            email="user1@example.com",
            hashed_password="pw1",
            full_name="User 1",
        )
        user_repo.create(
            organization_id=sample_organization.id,
            email="user2@example.com",
            hashed_password="pw2",
            full_name="User 2",
        )

        users = user_repo.list_by_organization(sample_organization.id)
        assert len(users) == 2

    def test_update_last_login(self, user_repo, sample_user):
        """Test updating last login timestamp"""
        assert sample_user.last_login_at is None

        user_repo.update_last_login(sample_user.id)

        user = user_repo.get_by_id(sample_user.id)
        assert user.last_login_at is not None
        assert isinstance(user.last_login_at, datetime)

    def test_multi_tenant_isolation(self, user_repo, org_repo):
        """Test users are isolated by organization"""
        org1 = org_repo.create(name="Org 1", slug="org-1")
        org2 = org_repo.create(name="Org 2", slug="org-2")

        user_repo.create(
            organization_id=org1.id,
            email="user@org1.com",
            hashed_password="pw",
            full_name="Org 1 User",
        )
        user_repo.create(
            organization_id=org2.id,
            email="user@org2.com",
            hashed_password="pw",
            full_name="Org 2 User",
        )

        org1_users = user_repo.list_by_organization(org1.id)
        org2_users = user_repo.list_by_organization(org2.id)

        assert len(org1_users) == 1
        assert len(org2_users) == 1
        assert org1_users[0].email == "user@org1.com"
        assert org2_users[0].email == "user@org2.com"


class TestTenderRepository:
    """Test TenderRepository operations"""

    def test_create_tender(self, tender_repo, sample_organization):
        """Test creating a tender"""
        tender = tender_repo.create(
            organization_id=sample_organization.id,
            title="AI Development Project",
            description="Need AI expertise",
            organization_name="Gov Agency",
            external_id="TEST-123",
            source="ted_europa",
            deadline="2025-06-01",
            estimated_value="€500,000",
        )

        assert tender.id is not None
        assert tender.external_id == "TEST-123"
        assert tender.status == TenderStatus.PENDING
        assert tender.is_deleted is False

    def test_get_by_organization(self, tender_repo, sample_organization, sample_tender):
        """Test retrieving tenders by organization"""
        tenders = tender_repo.list_by_organization(sample_organization.id)

        assert len(tenders) == 1
        assert tenders[0].id == sample_tender.id

    def test_get_by_organization_with_pagination(self, tender_repo, sample_organization):
        """Test pagination"""
        # Create 5 tenders
        for i in range(5):
            tender_repo.create(
                organization_id=sample_organization.id,
                title=f"Tender {i}",
                description=f"Description {i}",
                organization_name="Test Org",
                external_id=f"TEST-{i}",
                source="manual",
            )

        # Get first page (2 items)
        page1 = tender_repo.list_by_organization(sample_organization.id, limit=2, offset=0)
        assert len(page1) == 2

        # Get second page (2 items)
        page2 = tender_repo.list_by_organization(sample_organization.id, limit=2, offset=2)
        assert len(page2) == 2

        # Verify different results
        assert page1[0].id != page2[0].id

    def test_get_by_status(self, tender_repo, sample_organization):
        """Test filtering by status"""
        tender_repo.create(
            organization_id=sample_organization.id,
            title="Pending Tender",
            description="Pending desc",
            organization_name="Test Org",
            external_id="PENDING-1",
            source="manual",
            status=TenderStatus.PENDING,
        )
        tender_repo.create(
            organization_id=sample_organization.id,
            title="Completed Tender",
            description="Completed desc",
            organization_name="Test Org",
            external_id="COMPLETED-1",
            source="manual",
            status=TenderStatus.COMPLETE,
        )

        pending = tender_repo.list_by_organization(sample_organization.id, status=TenderStatus.PENDING)
        completed = tender_repo.list_by_organization(sample_organization.id, status=TenderStatus.COMPLETE)

        assert len(pending) == 1
        assert len(completed) == 1
        assert pending[0].status == TenderStatus.PENDING
        assert completed[0].status == TenderStatus.COMPLETE

    def test_update_status(self, tender_repo, sample_tender, sample_organization):
        """Test updating tender status"""
        tender_repo.update_status(sample_tender.id, TenderStatus.PROCESSING)

        tender = tender_repo.get_by_id(sample_tender.id, sample_organization.id)
        assert tender.status == TenderStatus.PROCESSING

    def test_find_by_external_id(self, tender_repo, sample_organization, sample_tender):
        """Test finding tender by external ID"""
        tender = tender_repo.get_by_external_id(
            "TEST-001", sample_organization.id
        )

        assert tender is not None
        assert tender.id == sample_tender.id

    def test_external_id_uniqueness_per_org(self, tender_repo, org_repo):
        """Test external_id is unique per organization"""
        org1 = org_repo.create(name="Org 1", slug="org-1")
        org2 = org_repo.create(name="Org 2", slug="org-2")

        # Same external_id in different orgs should work
        tender1 = tender_repo.create(
            organization_id=org1.id,
            title="Org 1 Tender",
            description="Description 1",
            organization_name="Org 1",
            external_id="SAME-ID",
            source="manual",
        )
        tender2 = tender_repo.create(
            organization_id=org2.id,
            title="Org 2 Tender",
            description="Description 2",
            organization_name="Org 2",
            external_id="SAME-ID",
            source="manual",
        )

        assert tender1.id != tender2.id
        assert tender1.external_id == tender2.external_id


class TestAnalysisRepository:
    """Test AnalysisRepository operations"""

    def test_create_analysis(self, analysis_repo, sample_tender):
        """Test creating an analysis result"""
        analysis = analysis_repo.create(
            tender_id=sample_tender.id,
            is_relevant=True,
            confidence=0.9,
            filter_categories=["AI", "Development"],
            filter_reasoning="Good match",
        )

        assert analysis.id is not None
        assert analysis.tender_id == sample_tender.id
        assert analysis.is_relevant is True
        assert analysis.confidence == 0.9

    def test_get_by_tender(self, analysis_repo, sample_tender):
        """Test retrieving analyses for a tender"""
        # Create analysis
        analysis_repo.create(
            tender_id=sample_tender.id,
            is_relevant=True,
            confidence=0.9,
        )

        analysis = analysis_repo.get_by_tender_id(sample_tender.id)
        assert analysis is not None

    def test_get_latest_by_tender(self, analysis_repo, sample_tender):
        """Test retrieving analysis by tender"""
        analysis = analysis_repo.create(
            tender_id=sample_tender.id,
            is_relevant=True,
            confidence=0.85,
        )

        result = analysis_repo.get_by_tender_id(sample_tender.id)
        assert result.id == analysis.id


class TestBidDocumentRepository:
    """Test BidDocumentRepository operations"""

    def test_create_bid_document(self, bid_doc_repo, sample_tender):
        """Test creating a bid document"""
        doc = bid_doc_repo.create(
            tender_id=sample_tender.id,
            executive_summary="Executive summary...",
            capabilities="Our capabilities",
            approach="Our approach",
            value_proposition="Our value",
        )

        assert doc.id is not None
        assert doc.tender_id == sample_tender.id
        assert "Executive summary" in doc.executive_summary

    def test_get_by_tender(self, bid_doc_repo, sample_tender):
        """Test retrieving documents for a tender"""
        bid_doc_repo.create(
            tender_id=sample_tender.id,
            executive_summary="Summary 1",
            capabilities="Cap 1",
            approach="App 1",
            value_proposition="Value 1",
        )

        doc = bid_doc_repo.get_by_tender_id(sample_tender.id)
        assert doc is not None

    def test_get_latest_by_tender(self, bid_doc_repo, sample_tender):
        """Test retrieving document by tender"""
        doc = bid_doc_repo.create(
            tender_id=sample_tender.id,
            executive_summary="Summary",
            capabilities="Capabilities",
            approach="Approach",
            value_proposition="Value",
        )

        result = bid_doc_repo.get_by_tender_id(sample_tender.id)
        assert result.id == doc.id

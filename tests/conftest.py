"""
Shared pytest fixtures and configuration for all tests
"""
import pytest

from procurement_ai.storage.database import Base, Database
from procurement_ai.storage.repositories import (
    OrganizationRepository,
    UserRepository,
    TenderRepository,
    AnalysisRepository,
    BidDocumentRepository,
)
from procurement_ai.storage.models import SubscriptionTier, UserRole, TenderStatus


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh in-memory SQLite database for each test.
    Fast and isolated - perfect for unit tests.
    """
    db = Database("sqlite:///:memory:")
    Base.metadata.create_all(db.engine)
    yield db
    Base.metadata.drop_all(db.engine)
    db.engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_db):
    """Provides a database session for tests"""
    with test_db.get_session() as session:
        yield session


@pytest.fixture(scope="function")
def org_repo(test_session):
    """OrganizationRepository instance"""
    return OrganizationRepository(test_session)


@pytest.fixture(scope="function")
def user_repo(test_session):
    """UserRepository instance"""
    return UserRepository(test_session)


@pytest.fixture(scope="function")
def tender_repo(test_session):
    """TenderRepository instance"""
    return TenderRepository(test_session)


@pytest.fixture(scope="function")
def analysis_repo(test_session):
    """AnalysisRepository instance"""
    return AnalysisRepository(test_session)


@pytest.fixture(scope="function")
def bid_doc_repo(test_session):
    """BidDocumentRepository instance"""
    return BidDocumentRepository(test_session)


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_organization(org_repo):
    """Create a sample organization"""
    return org_repo.create(
        name="Test Organization",
        slug="test-org",
        subscription_tier=SubscriptionTier.PRO,
    )


@pytest.fixture
def sample_user(user_repo, sample_organization):
    """Create a sample user"""
    return user_repo.create(
        organization_id=sample_organization.id,
        email="test@example.com",
        hashed_password="hashed_password_here",
        full_name="Test User",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def sample_tender(tender_repo, sample_organization):
    """Create a sample tender"""
    return tender_repo.create(
        organization_id=sample_organization.id,
        external_id="TEST-001",
        source="manual",
        title="AI-Powered Cybersecurity Platform",
        description="Government agency seeks AI-based threat detection system with real-time monitoring capabilities.",
        organization_name="National Cybersecurity Agency",
        deadline="2025-04-15",
        estimated_value="€2,000,000",
        status=TenderStatus.PENDING,
    )


# ============================================================================
# Mock LLM Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing agents without calling actual LLM"""
    return {
        "filter": {
            "is_match": True,
            "confidence": 0.85,
            "reasoning": "Strong match: AI, cybersecurity, government sector",
        },
        "rating": {
            "score": 90,
            "reasoning": "Excellent fit for AI services",
            "pros": ["Large contract", "Government client", "AI/ML focus"],
            "cons": ["Tight deadline", "Complex requirements"],
        },
        "proposal": "# Proposal for AI-Powered Cybersecurity Platform\n\nExecutive Summary...",
    }

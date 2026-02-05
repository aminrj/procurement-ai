#!/bin/bash
# Quick database setup for API testing.

set -e

echo "Setting up database for API testing"

export DATABASE_URL="${DATABASE_URL:-postgresql://procurement:procurement@localhost:5432/procurement}"

echo "Running migrations..."
alembic upgrade head

echo "Creating test organization..."
python - << 'PYEOF'
from procurement_ai.storage import Database
from procurement_ai.storage.repositories import OrganizationRepository
from procurement_ai.storage.models import SubscriptionTier

API_KEY = "test-org-key"

db = Database("postgresql://procurement:procurement@localhost:5432/procurement")

with db.get_session() as session:
    org_repo = OrganizationRepository(session)
    existing = org_repo.get_by_slug("test-org")

    if not existing:
        org = org_repo.create(
            name="Test Organization",
            slug="test-org",
            api_key=API_KEY,
            subscription_tier=SubscriptionTier.PRO,
        )
        org.monthly_analysis_limit = 2000
        session.commit()
        print(f"Created test organization: {org.name} (slug: {org.slug})")
        print(f"API Key: {org.api_key}")
        print(f"Monthly limit: {org.monthly_analysis_limit}")
    else:
        if existing.api_key != API_KEY:
            existing.api_key = API_KEY
            session.commit()
        print(f"Test organization already exists: {existing.name}")
        print(f"API Key: {existing.api_key}")
        print(f"Monthly limit: {existing.monthly_analysis_limit}")
PYEOF

echo ""
echo "Setup complete"
echo "API key for testing: test-org-key"
echo "Start API with: uvicorn procurement_ai.api.main:app --reload"

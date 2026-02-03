#!/bin/bash
# Quick database setup for API testing

set -e

echo "🔧 Setting up database for API testing..."

# Set environment for local connection
export DATABASE_URL="postgresql://procurement:procurement@localhost:5432/procurement"

# Run Alembic migrations
echo "Running migrations..."
alembic upgrade head

# Create test organization using Python
echo "Creating test organization..."
python - << 'EOF'
from procurement_ai.storage import Database
from procurement_ai.storage.repositories import OrganizationRepository
from procurement_ai.storage.models import SubscriptionTier

# Connect to database
db = Database("postgresql://procurement:procurement@localhost:5432/procurement")

with db.get_session() as session:
    org_repo = OrganizationRepository(session)
    
    # Check if test-org already exists
    existing = org_repo.get_by_slug("test-org")
    
    if not existing:
        # Create test organization
        org = org_repo.create(
            name="Test Organization",
            slug="test-org",
            subscription_tier=SubscriptionTier.PRO
        )
        # Update monthly limit
        org.monthly_analysis_limit = 2000
        session.commit()
        print(f"✅ Created test organization: {org.name} (slug: {org.slug})")
        print(f"   API Key: test-org")
        print(f"   Monthly limit: {org.monthly_analysis_limit}")
    else:
        print(f"✅ Test organization already exists: {existing.name}")
        print(f"   API Key: test-org")
        print(f"   Monthly limit: {existing.monthly_analysis_limit}")

EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "API Key for testing: test-org"
echo ""
echo "Start the API with:"
echo "  uvicorn procurement_ai.api.main:app --reload"
echo ""

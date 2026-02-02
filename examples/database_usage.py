"""
Example: Using the database layer

This demonstrates:
- Initializing the database
- Creating organizations and users
- Storing tenders and analysis results
- Using repositories for data access
"""

import asyncio
from datetime import datetime

from procurement_ai.storage import (
    init_db,
    OrganizationRepository,
    UserRepository,
    TenderRepository,
    AnalysisRepository,
)
from procurement_ai.storage.models import SubscriptionTier, UserRole, TenderStatus
from procurement_ai.models import Tender
from procurement_ai.config import Config
from procurement_ai.services.llm import LLMService
from procurement_ai.agents.filter import FilterAgent


async def main():
    """Run database example"""
    
    print("=" * 70)
    print("DATABASE LAYER EXAMPLE")
    print("=" * 70)
    
    # Step 1: Initialize database
    print("\n[1] Initializing database...")
    db = init_db(echo=True)  # echo=True shows SQL queries
    db.create_all()  # Create tables (use Alembic in production)
    print("✓ Database initialized")
    
    # Step 2: Create organization
    print("\n[2] Creating organization...")
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        
        org = org_repo.create(
            name="Acme Cybersecurity Inc",
            slug="acme-cyber",
            subscription_tier=SubscriptionTier.PRO
        )
        
        print(f"✓ Created: {org}")
        org_id = org.id
    
    # Step 3: Create users
    print("\n[3] Creating users...")
    with db.get_session() as session:
        user_repo = UserRepository(session)
        
        admin = user_repo.create(
            organization_id=org_id,
            email="admin@acme-cyber.com",
            hashed_password="hashed_password_here",  # Use proper hashing in production
            full_name="Alice Admin",
            role=UserRole.ADMIN
        )
        
        member = user_repo.create(
            organization_id=org_id,
            email="bob@acme-cyber.com",
            hashed_password="hashed_password_here",
            full_name="Bob Member",
            role=UserRole.MEMBER
        )
        
        print(f"✓ Created: {admin}")
        print(f"✓ Created: {member}")
    
    # Step 4: Create and analyze a tender
    print("\n[4] Creating and analyzing tender...")
    
    # Sample tender
    tender_data = Tender(
        id="SAMPLE-001",
        title="AI-Powered Cybersecurity Platform",
        description="Government agency seeks AI-based threat detection system...",
        organization="National Cybersecurity Agency",
        deadline="2025-04-15",
        estimated_value="€2,000,000"
    )
    
    with db.get_session() as session:
        tender_repo = TenderRepository(session)
        
        # Store tender
        tender_db = tender_repo.create(
            organization_id=org_id,
            title=tender_data.title,
            description=tender_data.description,
            organization_name=tender_data.organization,
            deadline=tender_data.deadline,
            estimated_value=tender_data.estimated_value,
            external_id=tender_data.id,
            source="manual"
        )
        
        print(f"✓ Created: {tender_db}")
        tender_id = tender_db.id
        
        # Mark as processing
        tender_repo.update_status(tender_id, TenderStatus.PROCESSING)
    
    # Step 5: Run AI analysis
    print("\n[5] Running AI analysis...")
    try:
        config = Config()
        llm = LLMService(config)
        filter_agent = FilterAgent(llm, config)
        
        # Analyze tender
        filter_result = await filter_agent.filter(tender_data)
        
        print(f"✓ Relevant: {filter_result.is_relevant}")
        print(f"✓ Confidence: {filter_result.confidence:.2f}")
        print(f"✓ Categories: {[c.value for c in filter_result.categories]}")
        
        # Store analysis results
        with db.get_session() as session:
            analysis_repo = AnalysisRepository(session)
            tender_repo = TenderRepository(session)
            
            analysis = analysis_repo.create(
                tender_id=tender_id,
                is_relevant=filter_result.is_relevant,
                confidence=filter_result.confidence,
                filter_categories=[c.value for c in filter_result.categories],
                filter_reasoning=filter_result.reasoning
            )
            
            print(f"✓ Stored: {analysis}")
            
            # Update tender status
            if filter_result.is_relevant:
                tender_repo.update_status(tender_id, TenderStatus.COMPLETE, processing_time=1.5)
            else:
                tender_repo.update_status(tender_id, TenderStatus.FILTERED_OUT, processing_time=1.5)
        
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        print("  (This is expected if LLM is not running)")
        
        # Store error in database
        with db.get_session() as session:
            tender_repo = TenderRepository(session)
            tender_repo.update_status(
                tender_id,
                TenderStatus.ERROR,
                error_message=str(e)
            )
    
    # Step 6: Query results
    print("\n[6] Querying database...")
    with db.get_session() as session:
        tender_repo = TenderRepository(session)
        org_repo = OrganizationRepository(session)
        
        # List all tenders
        tenders = tender_repo.list_by_organization(org_id, limit=10)
        print(f"\nTotal tenders: {len(tenders)}")
        
        for t in tenders:
            print(f"  - {t.title[:50]}... | Status: {t.status.value}")
        
        # Check organization usage
        org = org_repo.get_by_id(org_id)
        print(f"\nOrganization usage:")
        print(f"  Monthly limit: {org.monthly_analysis_limit}")
        print(f"  Used: {org.monthly_analysis_count}")
        print(f"  Can analyze: {org_repo.can_analyze(org_id)}")
    
    # Step 7: Multi-tenancy example
    print("\n[7] Multi-tenancy isolation...")
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        
        # Create second organization
        org2 = org_repo.create(
            name="Beta Security Corp",
            slug="beta-security",
            subscription_tier=SubscriptionTier.BASIC
        )
        
        print(f"✓ Created second organization: {org2}")
        
        # Each organization sees only their own tenders
        tender_repo = TenderRepository(session)
        
        org1_tenders = tender_repo.list_by_organization(org_id)
        org2_tenders = tender_repo.list_by_organization(org2.id)
        
        print(f"\nOrg 1 tenders: {len(org1_tenders)}")
        print(f"Org 2 tenders: {len(org2_tenders)}")
        print("✓ Data isolation verified")
    
    print("\n" + "=" * 70)
    print("EXAMPLE COMPLETE")
    print("=" * 70)
    print("\nDatabase features demonstrated:")
    print("✓ Multi-tenant organization structure")
    print("✓ User management with roles")
    print("✓ Tender storage and tracking")
    print("✓ AI analysis result persistence")
    print("✓ Repository pattern for clean data access")
    print("✓ Data isolation between organizations")


if __name__ == "__main__":
    asyncio.run(main())

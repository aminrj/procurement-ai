"""
Seed database with sample data for development

Usage:
    python examples/seed_database.py
"""

from procurement_ai.storage import init_db
from procurement_ai.storage.models import SubscriptionTier, UserRole
from procurement_ai.storage import (
    OrganizationRepository,
    UserRepository,
    TenderRepository,
)


def seed():
    """Seed database with demo organization, users, and tenders"""
    print("\n🌱 Seeding database with sample data...")
    
    db = init_db()
    
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        user_repo = UserRepository(session)
        tender_repo = TenderRepository(session)
        
        # Check if already seeded
        existing = org_repo.get_by_slug("demo-org")
        if existing:
            print("✓ Database already seeded (demo-org exists)")
            return
        
        # Create demo organization
        org = org_repo.create(
            name="Demo Organization",
            slug="demo-org",
            subscription_tier=SubscriptionTier.PRO
        )
        print(f"✓ Created organization: {org.name}")
        
        # Create demo users
        admin = user_repo.create(
            organization_id=org.id,
            email="admin@demo.local",
            hashed_password="$2b$12$demo_hashed_password",  # Placeholder
            full_name="Admin User",
            role=UserRole.ADMIN
        )
        print(f"✓ Created user: {admin.email} ({admin.role.value})")
        
        member = user_repo.create(
            organization_id=org.id,
            email="member@demo.local",
            hashed_password="$2b$12$demo_hashed_password",
            full_name="Member User",
            role=UserRole.MEMBER
        )
        print(f"✓ Created user: {member.email} ({member.role.value})")
        
        # Create sample tenders
        sample_tenders = [
            {
                "title": "AI-Powered Cybersecurity Platform Development",
                "description": "Government agency requires AI-powered threat detection and response system with ML capabilities.",
                "organization_name": "National Cyber Agency",
                "deadline": "2025-06-30",
                "estimated_value": "€2,500,000",
                "external_id": "DEMO-001",
            },
            {
                "title": "Cloud Migration Consulting Services",
                "description": "Enterprise needs cloud migration strategy and implementation for 500+ servers.",
                "organization_name": "Enterprise Corp",
                "deadline": "2025-05-15",
                "estimated_value": "€800,000",
                "external_id": "DEMO-002",
            },
            {
                "title": "Office Furniture Supply Contract",
                "description": "Supply ergonomic office furniture for 200 workstations with installation.",
                "organization_name": "Government Office",
                "deadline": "2025-04-01",
                "estimated_value": "€150,000",
                "external_id": "DEMO-003",
            },
        ]
        
        for tender_data in sample_tenders:
            tender = tender_repo.create(
                organization_id=org.id,
                source="demo",
                **tender_data
            )
            print(f"✓ Created tender: {tender.title}")
    
    print("\n✅ Database seeded successfully!")
    print("\nDemo credentials:")
    print("  Email: admin@demo.local (ADMIN)")
    print("  Email: member@demo.local (MEMBER)")
    print("  Password: (use proper authentication in production)")


if __name__ == "__main__":
    seed()

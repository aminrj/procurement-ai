#!/usr/bin/env python
"""
Fetch tenders from TED Europa and save to database

Simple script to populate your database with real tenders for AI analysis.
Keeps it simple - let the LLM Filter Agent do the filtering!
"""

from procurement_ai.scrapers import TEDScraper
from procurement_ai.storage import (
    init_db,
    OrganizationRepository,
    TenderRepository,
)
from procurement_ai.storage.models import SubscriptionTier


def main():
    """Fetch tenders and save to database."""
    print("=" * 70)
    print("TED SCRAPER → DATABASE")
    print("=" * 70)
    
    # Step 1: Initialize database
    print("\n[1] Initializing database...")
    
    # Use PostgreSQL (set DATABASE_URL env var, default to local PostgreSQL)
    import os
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/procurement_ai')
    
    db = init_db(database_url=db_url)
    db.create_all()  # Create tables if needed
    print(f"✓ Database ready")
    
    # Step 2: Ensure we have an organization
    print("\n[2] Setting up organization...")
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        
        # Check if demo org exists
        org = org_repo.get_by_slug("demo-org")
        
        if not org:
            org = org_repo.create(
                name="Demo Organization",
                slug="demo-org",
                subscription_tier=SubscriptionTier.PRO
            )
            print(f"✓ Created: {org.name}")
        else:
            print(f"✓ Using existing: {org.name}")
        
        org_id = org.id
    
    # Step 3: Fetch tenders from TED
    print("\n[3] Fetching tenders from TED Europa...")
    print("    (Limited to 10 tenders with full details)")
    
    try:
        with TEDScraper() as scraper:
            # Get basic list first
            tenders = scraper.search_tenders(
                days_back=7,    # Last week
                limit=10        # Limit to 10 to avoid spamming API
            )
            
            print(f"✓ Fetched {len(tenders)} tenders")
            
            # Now fetch full details for each
            print("\n[4] Fetching full details for each tender...")
            detailed_count = 0
            
            for i, tender in enumerate(tenders, 1):
                notice_id = tender.get('external_id')
                if notice_id:
                    print(f"   {i}/{len(tenders)} Fetching details for {notice_id}...", end='')
                    
                    details = scraper.get_tender_details(notice_id)
                    
                    if details:
                        # Update tender with full details
                        if details.get('title'):
                            tender['title'] = details['title']
                        if details.get('description'):
                            tender['description'] = details['description']
                        if details.get('buyer_name'):
                            tender['buyer_name'] = details['buyer_name']
                        if details.get('estimated_value'):
                            tender['estimated_value'] = details['estimated_value']
                        if details.get('deadline'):
                            tender['deadline'] = details['deadline']
                        
                        print(f" ✓")
                        detailed_count += 1
                    else:
                        print(f" (basic info only)")
            
            print(f"✓ Got full details for {detailed_count}/{len(tenders)} tenders")
        
    except Exception as e:
        print(f"❌ Error fetching tenders: {e}")
        print("\nMake sure you have internet connection to access TED API")
        return
    
    # Step 5: Save to database
    print("\n[5] Saving to database...")
    
    saved_count = 0
    skipped_count = 0
    
    with db.get_session() as session:
        tender_repo = TenderRepository(session)
        
        for tender_data in tenders:
            # Check if already exists (avoid duplicates)
            external_id = tender_data.get('external_id')
            
            if external_id:
                existing = tender_repo.get_by_external_id(external_id, org_id)
                if existing:
                    skipped_count += 1
                    continue
            
            # Create new tender
            try:
                tender = tender_repo.create(
                    organization_id=org_id,
                    title=tender_data['title'],
                    description=tender_data.get('description', tender_data['title']),
                    organization_name=tender_data.get('buyer_name', 'Unknown'),
                    deadline=tender_data.get('deadline'),
                    estimated_value=tender_data.get('estimated_value'),
                    external_id=external_id,
                    source='ted_europa',
                    url=tender_data.get('source_url')
                )
                saved_count += 1
                
            except Exception as e:
                print(f"⚠️  Error saving tender {external_id}: {e}")
                continue
    
    # Step 6: Summary
    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print(f"\n✓ Saved: {saved_count} new tenders with full details")
    print(f"⊘ Skipped: {skipped_count} duplicates")
    
    print("\n💡 Next steps:")
    print("   1. View data: python scripts/view_database.py")
    print("   2. Run AI analysis: python procurement_mvp.py")
    print("   3. Or use the API: python -m uvicorn src.procurement_ai.api.main:app")
    
    print("\n🎯 Tenders have real titles and descriptions for LLM analysis!")


if __name__ == "__main__":
    main()

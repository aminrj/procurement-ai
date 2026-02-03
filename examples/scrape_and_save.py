"""
Fetch tenders from TED Europa and save to database

Quick script to populate your database with real tenders for AI analysis.
"""
from procurement_ai.scrapers import TEDScraper
from procurement_ai.storage import init_db, TenderDB


def main():
    """Fetch tenders and save to database."""
    
    print("Fetching tenders from TED Europa...\n")
    
    try:
        # Fetch tenders
        with TEDScraper() as scraper:
            tenders = scraper.search_tenders(days_back=7, limit=50)
    except Exception as e:
        print(f"⚠️  Could not fetch from TED API: {str(e)[:150]}")
        print("\n" + "="*80)
        print("NOTE: TED Europa API may require updates or authentication.")
        print("="*80)
        print("\nFor now, you can:")
        print("1. Work with existing test data: python check_db.py")
        print("2. Focus on improving your AI agents with test data")
        print("3. Update the scraper when TED API access is confirmed")
        print("\nThe scraper infrastructure is ready - just needs API access!")
        return
    
    print(f"✓ Found {len(tenders)} tenders\n")
    
    if not tenders:
        print("No tenders found. Try again later.")
        return
    
    # Initialize database
    print("Saving to database...")
    db = init_db()
    
    saved_count = 0
    skipped_count = 0
    
    with db.get_session() as session:
        for tender_data in tenders:
            # Check if already exists
            existing = session.query(TenderDB).filter_by(
                external_id=tender_data['external_id']
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Create new tender
            tender = TenderDB(
                tenant_id='default',
                title=tender_data['title'],
                description=tender_data['description'],
                category=', '.join(tender_data['cpv_codes'][:2]),
                estimated_value=tender_data['estimated_value'],
                external_id=tender_data['external_id'],
                source=tender_data['source'],
                status='new'
            )
            session.add(tender)
            saved_count += 1
        
        session.commit()
    
    print(f"✓ Saved {saved_count} new tenders")
    if skipped_count:
        print(f"  Skipped {skipped_count} duplicates")
    
    print(f"\n💡 Now you can analyze these tenders:")
    print(f"   python examples/quickstart.py")


if __name__ == "__main__":
    main()

"""
Example: Scraping tenders from TED Europa

This script demonstrates how to:
1. Fetch tenders from TED Europa API
2. Filter by IT-related CPV codes
3. Display the results

For production use, integrate with TenderRepository to save to database.
"""
import sys
from datetime import datetime
from procurement_ai.scrapers import TEDScraper, ScraperError


def format_value(value):
    """Format tender value for display."""
    if value is None:
        return "Not specified"
    return f"€{value:,.0f}"


def main():
    """Fetch and display recent IT tenders."""
    
    print("=" * 80)
    print("TED Europa Tender Scraper - Example")
    print("=" * 80)
    print()
    
    # Configure search parameters
    days_back = 7  # Last 7 days
    limit = 20     # Max 20 results
    
    print(f"Searching for tenders from the last {days_back} days...")
    print()
    
    try:
        # Create scraper and fetch tenders
        with TEDScraper() as scraper:
            tenders = scraper.search_tenders(
                days_back=days_back,
                limit=limit
            )
        
        # Display results
        print(f"Found {len(tenders)} tender(s)\n")
        
        for i, tender in enumerate(tenders, 1):
            print(f"{i}. {tender['title']}")
            print(f"   ID: {tender['external_id']}")
            print(f"   Buyer: {tender['buyer_name']}")
            print(f"   Value: {format_value(tender['estimated_value'])}")
            print(f"   Deadline: {tender['deadline'] or 'Not specified'}")
            print(f"   CPV: {', '.join(tender['cpv_codes'][:3])}")
            if len(tender['cpv_codes']) > 3:
                print(f"        (+{len(tender['cpv_codes']) - 3} more)")
            print(f"   URL: {tender['source_url']}")
            print()
        
        if not tenders:
            print("No tenders found matching the criteria.")
            print("Try increasing days_back or checking TED Europa website.")
        
        # Integration example (commented out)
        print("\n" + "=" * 80)
        print("To save to database, integrate with TenderRepository:")
        print("=" * 80)
        print("""
from procurement_ai.models import DatabaseManager, TenderDB

# Initialize database
db_manager = DatabaseManager(config.DATABASE_URL)
db_manager.init_database()

# Save tenders
with db_manager.get_session() as session:
    for tender_data in tenders:
        # Check if already exists
        existing = session.query(TenderDB).filter_by(
            external_id=tender_data['external_id']
        ).first()
        
        if not existing:
            tender = TenderDB(
                tenant_id='default',  # or your tenant ID
                title=tender_data['title'],
                description=tender_data['description'],
                category=', '.join(tender_data['cpv_codes'][:2]),
                estimated_value=tender_data['estimated_value'],
                external_id=tender_data['external_id'],
                source=tender_data['source']
            )
            session.add(tender)
    
    session.commit()
        """)
        
    except ScraperError as e:
        print(f"❌ Scraper error: {e}")
        print("\nPossible causes:")
        print("- TED API is temporarily unavailable")
        print("- Network connectivity issues")
        print("- Rate limiting (try again in a few minutes)")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

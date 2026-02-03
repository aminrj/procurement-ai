#!/usr/bin/env python
"""
View tenders in the database

Quick script to see what data we have.
"""

import os
import sys

# Add src to path
sys.path.insert(0, '/Users/ARAJI/git/ai_projects/procurement-ai/src')

from procurement_ai.storage import init_db, TenderRepository


def main():
    """View database contents"""
    print("=" * 70)
    print("DATABASE CONTENTS")
    print("=" * 70)
    
    # Initialize database
    db_url = os.getenv('DATABASE_URL', 'sqlite:///procurement_ai.db')
    db = init_db(database_url=db_url)
    
    # Get tenders
    with db.get_session() as session:
        tender_repo = TenderRepository(session)
        
        # Get all tenders for org_id=1 (demo org)
        tenders = tender_repo.list_by_organization(org_id=1, limit=50)
        
        print(f"\n📊 Found {len(tenders)} tenders\n")
        
        for i, tender in enumerate(tenders[:10], 1):
            print(f"{i}. {tender.title}")
            print(f"   Org: {tender.organization_name}")
            if tender.description:
                desc_preview = tender.description[:200].replace('\n', ' ')
                print(f"   Desc: {desc_preview}...")
            print(f"   Source: {tender.source}")
            print(f"   ID: {tender.external_id}")
            print(f"   Status: {tender.status.value}")
            if tender.url:
                print(f"   URL: {tender.url[:60]}...")
            print()
        
        if len(tenders) > 10:
            print(f"... and {len(tenders) - 10} more")
    
    print("\n💡 Next: Run AI analysis on these tenders")
    print("   python procurement_mvp.py")


if __name__ == "__main__":
    main()

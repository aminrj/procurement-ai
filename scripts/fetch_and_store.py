#!/usr/bin/env python
"""Fetch tenders from TED and store them in the database."""

import os

from procurement_ai.scrapers import TEDScraper
from procurement_ai.storage import OrganizationRepository, TenderRepository, init_db
from procurement_ai.storage.models import SubscriptionTier


def main():
    print("=" * 70)
    print("TED SCRAPER TO DATABASE")
    print("=" * 70)

    print("\n[1] Initializing database")
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://procurement:procurement@localhost:5432/procurement",
    )
    db = init_db(database_url=db_url)
    db.create_all()
    print("Database ready")

    print("\n[2] Setting up organization")
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        org = org_repo.get_by_slug("demo-org")

        if not org:
            org = org_repo.create(
                name="Demo Organization",
                slug="demo-org",
                api_key="demo-org-key",
                subscription_tier=SubscriptionTier.PRO,
            )
            print(f"Created organization: {org.name}")
        else:
            print(f"Using existing organization: {org.name}")

        org_id = org.id

    print("\n[3] Fetching tenders from TED")
    print("    (limit=10 with detail enrichment)")

    try:
        with TEDScraper() as scraper:
            tenders = scraper.search_tenders(days_back=7, limit=10)
            print(f"Fetched {len(tenders)} tenders")

            print("\n[4] Fetching details")
            detailed_count = 0
            for i, tender in enumerate(tenders, 1):
                notice_id = tender.get("external_id")
                if not notice_id:
                    continue

                print(f"   {i}/{len(tenders)} Fetching details for {notice_id}...", end="")
                details = scraper.get_tender_details(notice_id)
                if details:
                    if details.get("title"):
                        tender["title"] = details["title"]
                    if details.get("description"):
                        tender["description"] = details["description"]
                    if details.get("organization"):
                        tender["buyer_name"] = details["organization"]
                    if details.get("estimated_value"):
                        tender["estimated_value"] = details["estimated_value"]
                    if details.get("deadline"):
                        tender["deadline"] = details["deadline"]
                    detailed_count += 1
                    print(" done")
                else:
                    print(" skipped")

            print(f"Detailed records: {detailed_count}/{len(tenders)}")

    except Exception as exc:
        print(f"Error fetching tenders: {exc}")
        print("Check network access and TED API availability")
        return

    print("\n[5] Saving to database")
    saved_count = 0
    skipped_count = 0

    with db.get_session() as session:
        tender_repo = TenderRepository(session)

        for tender_data in tenders:
            external_id = tender_data.get("external_id")
            if external_id:
                existing = tender_repo.get_by_external_id(external_id, org_id)
                if existing:
                    skipped_count += 1
                    continue

            try:
                tender_repo.create(
                    organization_id=org_id,
                    title=tender_data["title"],
                    description=tender_data.get("description", tender_data["title"]),
                    organization_name=tender_data.get("buyer_name", "Unknown"),
                    deadline=tender_data.get("deadline"),
                    estimated_value=tender_data.get("estimated_value"),
                    external_id=external_id,
                    source="ted_europa",
                    url=tender_data.get("source_url"),
                )
                saved_count += 1
            except Exception as exc:
                print(f"   Error saving tender {external_id}: {exc}")

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Saved: {saved_count}")
    print(f"Skipped duplicates: {skipped_count}")
    print("\nNext steps:")
    print("  1. View data: python scripts/view_database.py")
    print("  2. Run AI analysis: python procurement_mvp.py")
    print("  3. Start API: uvicorn procurement_ai.api.main:app --reload")


if __name__ == "__main__":
    main()

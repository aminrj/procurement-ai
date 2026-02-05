#!/usr/bin/env python
"""View tenders currently stored in the database."""

import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from procurement_ai.config import Config
from procurement_ai.storage import OrganizationRepository, TenderRepository, init_db


def main():
    print("=" * 70)
    print("DATABASE CONTENTS")
    print("=" * 70)

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://procurement:procurement@localhost:5432/procurement",
    )
    db = init_db(database_url=db_url)

    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        tender_repo = TenderRepository(session)

        org = org_repo.get_by_slug(Config.WEB_ORGANIZATION_SLUG)
        if not org:
            print("No organization found for configured web slug")
            return

        tenders = tender_repo.list_by_organization(org_id=org.id, limit=50)
        print(f"\nFound {len(tenders)} tenders for organization '{org.slug}'\n")

        for i, tender in enumerate(tenders[:10], 1):
            print(f"{i}. {tender.title}")
            print(f"   Organization: {tender.organization_name}")
            if tender.description:
                desc_preview = tender.description[:200].replace("\n", " ")
                print(f"   Description: {desc_preview}...")
            print(f"   Source: {tender.source}")
            print(f"   External ID: {tender.external_id}")
            print(f"   Status: {tender.status.value}")
            if tender.url:
                print(f"   URL: {tender.url[:80]}...")
            print()

        if len(tenders) > 10:
            print(f"... and {len(tenders) - 10} more")

    print("\nNext step: run AI analysis with python procurement_mvp.py")


if __name__ == "__main__":
    main()

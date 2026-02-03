# Scripts

Utility scripts for managing the Procurement AI system.

## Quick Start

```bash
# Fetch tenders and populate database
./scripts/quickstart.sh
```

This will:
1. Fetch 50 recent tenders from TED Europa
2. Save them to SQLite database
3. Show you what's in the database

## Individual Scripts

### `fetch_and_store.py`
Fetch tenders from TED Europa API and save to database.

```bash
PYTHONPATH=src:$PYTHONPATH python scripts/fetch_and_store.py
```

**What it does:**
- Creates database tables if needed
- Fetches recent tenders (last 7 days)
- Stores them with organization isolation
- Avoids duplicates

**Configuration:**
- Default: SQLite (`procurement_ai.db`)
- PostgreSQL: Set `DATABASE_URL` environment variable

### `view_database.py`
View what tenders are in your database.

```bash
PYTHONPATH=src:$PYTHONPATH python scripts/view_database.py
```

**Shows:**
- Total tender count
- First 10 tenders with details
- Status and source information

### `ted_scraper_minimal.py`
Standalone TED scraper for testing (no dependencies on main codebase).

```bash
python scripts/ted_scraper_minimal.py --days 7 --limit 20
```

**Use cases:**
- Testing TED API connectivity
- Quick tender search without database
- Debugging scraper issues

### `init_db.sh`
Initialize PostgreSQL database with schema.

```bash
./scripts/init_db.sh
```

Requires: PostgreSQL installed and running

### `test_api.sh`
Test the REST API endpoints.

```bash
./scripts/test_api.sh
```

Requires: API server running on port 8000

## Environment Variables

- `DATABASE_URL` - Database connection string
  - Default: `sqlite:///procurement_ai.db`
  - PostgreSQL: `postgresql://user:pass@localhost/procurement_ai`

- `PYTHONPATH` - Add `src` directory for imports
  - `export PYTHONPATH=/path/to/project/src:$PYTHONPATH`

## Database File

The SQLite database file `procurement_ai.db` is created in the project root.

**Location:** `/Users/ARAJI/git/ai_projects/procurement-ai/procurement_ai.db`

**Schema:**
- organizations
- users  
- tenders
- analysis_results
- bid_documents

## Notes

**LLM Filtering Philosophy:**
We fetch ALL recent tenders and let the LLM Filter Agent identify relevant ones. This is:
- Simpler than complex filtering logic
- More flexible (LLM understands context better than keywords)
- More accurate (natural language understanding)

**Next Steps:**
After populating database with tenders:
1. Run AI analysis: `python procurement_mvp.py`
2. Start API: `uvicorn src.procurement_ai.api.main:app`
3. Access at: `http://localhost:8000/docs`

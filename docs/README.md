# Procurement AI - Documentation

## Quick Start

### 1. Fetch Tenders
```bash
# Get recent tenders from TED Europa
python scripts/ted_scraper_minimal.py --limit 10

# Or use the main scraper
python examples/scrape_tenders.py
```

### 2. Run AI Analysis
```bash
# Analyze tenders and generate proposals
python procurement_mvp.py
```

### 3. Check Results
```bash
# View tenders in database
python check_db.py
```

## Key Components

### Scraper (`src/procurement_ai/scrapers/ted_scraper.py`)
- Fetches tenders from TED Europa API
- Returns: ID, date, country, buyer
- For full details: use `get_tender_details(notice_id)`

### AI Agents (`src/procurement_ai/agents/`)
1. **Filter** - Classifies tender relevance (cybersecurity, AI, software)
2. **Rating** - Scores our capability (1-10)
3. **Generator** - Creates bid proposals

### Models (`src/procurement_ai/models.py`)
- `Tender`: Input data (title, description, organization, deadline, value)
- `FilterResult`, `RatingResult`, `BidDocument`: Agent outputs

## Database

SQLite database with tenders and analysis results:
```python
from procurement_ai.storage import DatabaseManager

db = DatabaseManager()
tenders = db.get_all_tenders()
```

## Configuration

Set environment variables or edit `.env`:
```bash
OPENAI_API_KEY=your-key
DATABASE_URL=sqlite:///procurement.db
```

## Testing

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/unit/test_agents.py
```

## Architecture

```
User Request
    ↓
TED Scraper → Fetch Tenders → Database
    ↓
Filter Agent → Relevant? → If Yes ↓
Rating Agent → Score → If High ↓
Document Generator → Proposal
    ↓
Results
```

## For Production

1. **Scale**: Add pagination, batch processing
2. **Enrich**: Parse XML for full tender details
3. **Monitor**: Add logging, error tracking
4. **Deploy**: Docker containers (see `deployment/`)

Last updated: February 3, 2026
